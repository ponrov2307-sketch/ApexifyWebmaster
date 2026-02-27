import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from datetime import datetime
from contextlib import contextmanager

# โหลดตัวแปรจากไฟล์ .env
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# 🌟 1. สร้าง Connection Pool (บ่อพัก) รองรับคนเข้าพร้อมกัน 1-20 ท่อ
try:
    if DB_URL:
        db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, DB_URL)
    else:
        db_pool = None
        print("❌ Error: ไม่พบ DATABASE_URL ในไฟล์ .env")
except Exception as e:
    db_pool = None
    print(f"❌ Error creating Connection Pool: {e}")

@contextmanager
def get_db_connection():
    """Context Manager: ระบบเบิก-คืน Database Connection อัตโนมัติ"""
    conn = None
    try:
        if db_pool:
            conn = db_pool.getconn()
        else:
            conn = psycopg2.connect(DB_URL)
        yield conn
    finally:
        if conn:
            if db_pool:
                db_pool.putconn(conn) # 🌟 ใช้เสร็จเอาไปคืนในบ่อให้คนอื่นใช้ต่อ
            else:
                conn.close()

def get_user_by_telegram(telegram_id: int):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # 🌟 ถอด username ออก เพื่อไม่ให้เกิด Error column does not exist
            c.execute("SELECT user_id, status, role, expiry_date FROM users WHERE user_id = %s", (str(telegram_id),))
            row = c.fetchone()
            c.close()
            
        if row:
            expiry = row[3]
            expiry_str = expiry.strftime('%d/%m/%Y') if isinstance(expiry, datetime) else str(expiry) if expiry else None
            
            # 🌟 สร้างชื่อจำลองจาก 4 ตัวท้ายของ ID เหมือนเดิม
            safe_username = f"User_{str(telegram_id)[-4:]}"
            
            return {
                'user_id': row[0],
                'username': safe_username, 
                'status': row[1] if row[1] else 'active',
                'role': row[2] if row[2] else 'free',
                'vip_expiry': expiry_str 
            }
        return None
    except Exception as e:
        print(f"❌ DB Error (get_user_by_telegram): {e}")
        return None

def get_portfolio(user_id: str):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT ticker, shares, avg_cost, asset_group FROM portfolios WHERE user_id = %s", (str(user_id),))
            rows = c.fetchall()
            c.close()
            
        portfolio = []
        for row in rows:
            portfolio.append({
                'ticker': row[0],
                'shares': float(row[1]),
                'avg_cost': float(row[2]),
                'asset_group': row[3] if len(row) > 3 else 'ALL'
            })
        return portfolio
    except Exception as e:
        print(f"❌ DB Error (get_portfolio): {e}")
        return []

def get_all_unique_tickers():
    """🌟 ดึงรายชื่อหุ้น 'ทั้งหมดที่มีในระบบ' โดยไม่ซ้ำกัน (สำหรับ Global Cache)"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT ticker FROM portfolios")
            rows = c.fetchall()
            c.close()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"❌ DB Error (get_all_unique_tickers): {e}")
        return []

def add_portfolio_stock(user_id: str, ticker: str, shares: float, avg_cost: float, asset_group: str = 'ALL'):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            ticker = ticker.upper().strip()
            c.execute("SELECT shares, avg_cost FROM portfolios WHERE user_id = %s AND ticker = %s", (str(user_id), ticker))
            row = c.fetchone()
            
            if row:
                old_shares = float(row[0])
                old_cost = float(row[1])
                new_shares = old_shares + float(shares)
                new_avg_cost = ((old_shares * old_cost) + (float(shares) * float(avg_cost))) / new_shares
                
                c.execute("UPDATE portfolios SET shares = %s, avg_cost = %s, asset_group = %s WHERE user_id = %s AND ticker = %s",
                          (new_shares, new_avg_cost, asset_group, str(user_id), ticker))
            else:
                # 🌟 บันทึก Group ลงฐานข้อมูลด้วย
                c.execute("INSERT INTO portfolios (user_id, ticker, shares, avg_cost, asset_group) VALUES (%s, %s, %s, %s, %s)",
                          (str(user_id), ticker, float(shares), float(avg_cost), asset_group))
            conn.commit()
            c.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (add_portfolio_stock): {e}")
        return False
def update_portfolio_stock(user_id: str, ticker: str, shares: float, avg_cost: float, asset_group: str = 'ALL'):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE portfolios SET shares = %s, avg_cost = %s, asset_group = %s WHERE user_id = %s AND ticker = %s",
                      (float(shares), float(avg_cost), asset_group, str(user_id), ticker.upper()))
            conn.commit()
            c.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (update_portfolio): {e}")
        return False

def delete_portfolio_stock(user_id: str, ticker: str):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM portfolios WHERE user_id = %s AND ticker = %s", (str(user_id), ticker.upper()))
            conn.commit()
            c.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (delete_portfolio): {e}")
        return False