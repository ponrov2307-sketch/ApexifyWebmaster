"""
⚠️ วิธีการสร้างตารางใน Supabase:
1. เข้าไปที่เว็บ Supabase -> โปรเจกต์ของคุณ -> เมนู SQL Editor
2. ก๊อปปี้คำสั่ง SQL ด้านล่างนี้ไปรัน เพื่อสร้างตารางทั้งหมดในคลิกเดียว

--- ก๊อปปี้ตั้งแต่บรรทัดนี้ไปรันใน Supabase ---
CREATE TABLE apex_users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    username TEXT,
    is_vip BOOLEAN DEFAULT FALSE,
    vip_expiry TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE apex_portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES apex_users(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    shares NUMERIC NOT NULL,
    avg_cost NUMERIC NOT NULL,
    asset_group TEXT DEFAULT 'ALL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE apex_portfolio_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES apex_users(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    total_value NUMERIC NOT NULL,
    UNIQUE(user_id, record_date)
);
--- สิ้นสุดคำสั่ง SQL ---
"""

from core.database import db

# --- ฟังก์ชันตัวช่วยดึงข้อมูล (Helper Functions) ---
# เขียนเตรียมไว้เพื่อให้หน้าเว็บและบอทเรียกใช้งานได้ง่ายๆ บรรทัดเดียวจบ

def get_user_by_telegram(telegram_id: int):
    """ดึงข้อมูลลูกค้าจาก Telegram ID"""
    if not db: return None
    res = db.table('apex_users').select('*').eq('telegram_id', telegram_id).execute()
    return res.data[0] if res.data else None

def get_portfolio(user_id: int):
    """ดึงพอร์ตหุ้นทั้งหมดของลูกค้ารายนั้น"""
    if not db: return []
    res = db.table('apex_portfolios').select('*').eq('user_id', user_id).execute()
    return res.data