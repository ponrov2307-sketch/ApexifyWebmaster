import os
import psycopg2
from dotenv import load_dotenv

# โหลดตัวแปรจากไฟล์ .env (ให้แน่ใจว่าในไฟล์ .env มี DATABASE_URL ของคุณอยู่)
load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

def get_connection():
    """เชื่อมต่อกับ PostgreSQL (ฐานข้อมูลเดียวกับบอทหลัก)"""
    if not DB_URL:
        print("❌ Error: ไม่พบ DATABASE_URL ในไฟล์ .env")
    return psycopg2.connect(DB_URL)

def get_user_by_telegram(telegram_id: int):
    """ดึงข้อมูลลูกค้าจาก Telegram ID"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT user_id, status, role FROM users WHERE user_id = %s", (str(telegram_id),))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {'user_id': row[0], 'status': row[1], 'role': row[2]}
        return None
    except Exception as e:
        print(f"❌ DB Error (get_user_by_telegram): {e}")
        return None

def get_portfolio(user_id: str):
    """ดึงพอร์ตหุ้นทั้งหมดของลูกค้ารายนั้น"""
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
    """แก้ไขข้อมูลจำนวนหุ้นและราคาต้นทุน"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE portfolios SET shares = %s, avg_cost = %s WHERE user_id = %s AND ticker = %s",
                  (float(shares), float(avg_cost), str(user_id), ticker.upper()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (update_portfolio_stock): {e}")
        return False

def delete_portfolio_stock(user_id: str, ticker: str):
    """ลบหุ้นออกจากพอร์ต"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM portfolios WHERE user_id = %s AND ticker = %s",
                  (str(user_id), ticker.upper()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (delete_portfolio_stock): {e}")
        return False