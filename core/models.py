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
                db_pool.putconn(conn)
            else:
                conn.close()

def get_user_by_telegram(telegram_id: int):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, status, role, expiry_date, username FROM users WHERE user_id = %s", (str(telegram_id),))
            row = c.fetchone()
            c.close()
            
        if row:
            expiry = row[3]
            expiry_str = expiry.strftime('%d/%m/%Y') if isinstance(expiry, datetime) else str(expiry) if expiry else None
            role = row[2] if row[2] else 'free'
            
            # 🌟 เช็ควันหมดอายุแบบ Real-time ให้หน้าเว็บ
            if role in ['vip', 'pro'] and expiry:
                try:
                    exp_dt = datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S') if isinstance(expiry, str) else expiry
                    if datetime.now() > exp_dt:
                        role = 'free' # หมดอายุให้กลายเป็นฟรีทันที
                except: pass

            db_username = row[4] if len(row) > 4 and row[4] else f"User_{str(telegram_id)[-4:]}"
            
            return {
                'user_id': row[0], 'username': db_username, 
                'status': row[1] if row[1] else 'active',
                'role': role, 'vip_expiry': expiry_str 
            }
        return None
    except Exception as e:
        print(f"❌ DB Error (get_user_by_telegram): {e}")
        return None


def get_user_by_username(username: str):
    """Look up a user by their username (case-insensitive)."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, status, role, expiry_date, username FROM users WHERE LOWER(username) = LOWER(%s)", (username,))
            row = c.fetchone()
            c.close()

        if row:
            expiry = row[3]
            expiry_str = expiry.strftime('%d/%m/%Y') if isinstance(expiry, datetime) else str(expiry) if expiry else None
            role = row[2] if row[2] else 'free'

            if role in ['vip', 'pro'] and expiry:
                try:
                    exp_dt = datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S') if isinstance(expiry, str) else expiry
                    if datetime.now() > exp_dt:
                        role = 'free'
                except: pass

            db_username = row[4] if len(row) > 4 and row[4] else username

            return {
                'user_id': row[0], 'username': db_username,
                'status': row[1] if row[1] else 'active',
                'role': role, 'vip_expiry': expiry_str
            }
        return None
    except Exception as e:
        print(f"❌ DB Error (get_user_by_username): {e}")
        return None


def get_portfolio(user_id: str):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # ดึงข้อมูลมาให้ครบ รวมถึง Group และ Alert Price
            c.execute("SELECT ticker, shares, avg_cost, asset_group, alert_price FROM portfolios WHERE user_id = %s", (str(user_id),))
            rows = c.fetchall()
            c.close()
            
        portfolio = []
        for row in rows:
            portfolio.append({
                'ticker': row[0],
                'shares': float(row[1]),
                'avg_cost': float(row[2]),
                'asset_group': row[3] if len(row) > 3 and row[3] else 'ALL',
                'alert_price': float(row[4]) if len(row) > 4 and row[4] else 0.0
            })
        return portfolio
    except Exception as e:
        print(f"❌ DB Error (get_portfolio): {e}")
        return []

def get_all_unique_tickers():
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
                c.execute("INSERT INTO portfolios (user_id, ticker, shares, avg_cost, asset_group, alert_price) VALUES (%s, %s, %s, %s, %s, 0)",
                          (str(user_id), ticker, float(shares), float(avg_cost), asset_group))
            conn.commit()
            c.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (add_portfolio_stock): {e}")
        return False

def update_portfolio_stock(user_id: str, ticker: str, shares: float, avg_cost: float, asset_group: str = 'ALL', alert_price: float = 0.0):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE portfolios 
                SET shares = %s, avg_cost = %s, asset_group = %s, alert_price = %s 
                WHERE user_id = %s AND ticker = %s
            """, (float(shares), float(avg_cost), asset_group, float(alert_price), str(user_id), ticker.upper()))
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

def get_all_active_alerts():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, ticker, alert_price FROM portfolios WHERE alert_price > 0")
            rows = c.fetchall()
            c.close()
        return [{"user_id": r[0], "ticker": r[1], "alert_price": float(r[2])} for r in rows]
    except Exception as e:
        print(f"❌ DB Error (get_all_active_alerts): {e}")
        return []

def clear_stock_alert(user_id: str, ticker: str):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE portfolios SET alert_price = 0 WHERE user_id = %s AND ticker = %s", (str(user_id), ticker.upper()))
            conn.commit()
            c.close()
    except Exception as e:
        pass
def get_user_price_alerts(user_id: str):
    """ดึงข้อมูลการตั้งเตือนราคาจากตาราง user_price_alerts"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, symbol, target_price, condition, is_active FROM user_price_alerts WHERE user_id = %s ORDER BY is_active DESC, id DESC", (str(user_id),))
            rows = c.fetchall()
            c.close()
        return [{"id": r[0], "symbol": r[1], "target_price": float(r[2]), "condition": r[3], "is_active": int(r[4])} for r in rows]
    except Exception as e:
        print(f"❌ DB Error (get_user_price_alerts): {e}")
        return []

def delete_price_alert(alert_id: int):
    """ลบการตั้งเตือนราคา"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM user_price_alerts WHERE id = %s", (alert_id,))
            conn.commit()
            c.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (delete_price_alert): {e}")
        return False    
def set_user_price_alert(user_id: str, symbol: str, target_price: float, condition: str):
    """บันทึกแจ้งเตือนลงตาราง user_price_alerts ที่บอท Telegram ใช้"""
    if target_price <= 0: return False
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # เช็คว่ามี alert ของหุ้นตัวนี้ที่ยัง active อยู่ไหม
            c.execute("SELECT id FROM user_price_alerts WHERE user_id = %s AND symbol = %s AND is_active = 1", (str(user_id), symbol.upper()))
            row = c.fetchone()
            
            if row:
                # ถ้ามีอยู่แล้ว ให้อัปเดตราคาเป้าหมายใหม่
                c.execute("UPDATE user_price_alerts SET target_price = %s, condition = %s WHERE id = %s", (float(target_price), condition, row[0]))
            else:
                # ถ้ายังไม่มี ให้สร้างใหม่
                c.execute("INSERT INTO user_price_alerts (user_id, symbol, target_price, condition, is_active) VALUES (%s, %s, %s, %s, 1)",
                          (str(user_id), symbol.upper(), float(target_price), condition))
            conn.commit()
            c.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (set_user_price_alert): {e}")
        return False


# ─── Watchlist ───

def _ensure_watchlist_table():
    """Create watchlist table if it doesn't exist."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS user_watchlist (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(64) NOT NULL,
                    ticker VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, ticker)
                )
            """)
            conn.commit()
            c.close()
    except Exception as e:
        print(f"❌ DB Error (ensure_watchlist_table): {e}")


def get_user_watchlist(user_id: str) -> list[str]:
    _ensure_watchlist_table()
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT ticker FROM user_watchlist WHERE user_id = %s ORDER BY created_at", (str(user_id),))
            rows = c.fetchall()
            c.close()
        return [r[0] for r in rows]
    except Exception as e:
        print(f"❌ DB Error (get_user_watchlist): {e}")
        return []


def add_watchlist_item(user_id: str, ticker: str):
    _ensure_watchlist_table()
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO user_watchlist (user_id, ticker) VALUES (%s, %s) ON CONFLICT DO NOTHING", (str(user_id), ticker.upper()))
            conn.commit()
            c.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (add_watchlist_item): {e}")
        return False


def remove_watchlist_item(user_id: str, ticker: str):
    _ensure_watchlist_table()
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM user_watchlist WHERE user_id = %s AND ticker = %s", (str(user_id), ticker.upper()))
            conn.commit()
            c.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (remove_watchlist_item): {e}")
        return False


# ─── Online Presence ───

def _ensure_last_seen_column():
    """Add last_seen column to users table if it doesn't exist."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP")
            conn.commit()
            c.close()
    except Exception as e:
        print(f"❌ DB Error (ensure_last_seen): {e}")


def update_user_last_seen(user_id: str):
    _ensure_last_seen_column()
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET last_seen = NOW() WHERE user_id = %s", (str(user_id),))
            conn.commit()
            c.close()
        return True
    except Exception as e:
        print(f"❌ DB Error (update_user_last_seen): {e}")
        return False


def get_online_users():
    _ensure_last_seen_column()
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT user_id, username, role, status, last_seen
                FROM users
                WHERE last_seen >= NOW() - INTERVAL '75 seconds'
                ORDER BY last_seen DESC
            """)
            rows = c.fetchall()
            c.close()
        return [
            {
                "user_id": r[0],
                "username": r[1] or f"User_{str(r[0])[-4:]}",
                "role": r[2] or "free",
                "status": r[3] or "active",
                "last_seen": (r[4].isoformat() + "Z") if r[4] else None,
            }
            for r in rows
        ]
    except Exception as e:
        print(f"❌ DB Error (get_online_users): {e}")
        return []