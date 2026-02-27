import os
import psycopg2
from dotenv import load_dotenv

# โหลดตัวแปรจากไฟล์ .env
load_dotenv()

# ลิงก์ฐานข้อมูล (ใช้ลิงก์เดียวกับที่บอท Telegram ใช้เป๊ะ)
DB_URL = os.getenv("DATABASE_URL")

def get_connection():
    """เชื่อมต่อกับ PostgreSQL โดยตรงด้วย SQL (วิธีเดียวกับบอท)"""
    if not DB_URL:
        print("❌ Error: ไม่พบ DATABASE_URL ในไฟล์ .env")
    return psycopg2.connect(DB_URL)

def get_user_by_telegram(telegram_id: int):
    """ดึงข้อมูลลูกค้าจาก Telegram ID (ชี้เป้าตาราง users ของบอท)"""
    try:
        conn = get_connection()
        c = conn.cursor()
        
        # 🎯 ใช้ SQL ตรงๆ เหมือนไฟล์ database.py ของบอท
        c.execute("SELECT user_id, status, role, expiry_date FROM users WHERE user_id = %s", (str(telegram_id),))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'username': f"User_{str(telegram_id)[-4:]}", # บอทไม่มี username ใช้เลข ID แทน
                'status': row[1] if row[1] else 'active',
                'role': row[2] if row[2] else 'free',
                'vip_expiry': row[3] # ดึงจากคอลัมน์ expiry_date ของบอทเก่า
            }
        return None
    except Exception as e:
        print(f"❌ DB Error (get_user_by_telegram): {e}")
        return None

def get_portfolio(user_id: str):
    """ดึงพอร์ตหุ้น (จากตาราง portfolios)"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT ticker, shares, avg_cost FROM portfolios WHERE user_id = %s", (str(user_id),))
        rows = c.fetchall()
        conn.close()
        
        portfolio = []
        for row in rows:
            portfolio.append({
                'ticker': row[0],
                'shares': float(row[1]),
                'avg_cost': float(row[2])
            })
        return portfolio
    except Exception as e:
        print(f"❌ DB Error (get_portfolio): {e}")
        return []

def update_portfolio_stock(user_id: str, ticker: str, shares: float, avg_cost: float):
    """แก้ไขจำนวนหุ้นและต้นทุนผ่านเว็บ"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE portfolios SET shares = %s, avg_cost = %s WHERE user_id = %s AND ticker = %s",
                  (float(shares), float(avg_cost), str(user_id), ticker.upper()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (update_portfolio): {e}")
        return False

def delete_portfolio_stock(user_id: str, ticker: str):
    """ลบหุ้นออกจากพอร์ตผ่านเว็บ"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM portfolios WHERE user_id = %s AND ticker = %s",
                  (str(user_id), ticker.upper()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (delete_portfolio): {e}")
        return False