from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import yfinance as yf
from datetime import datetime, timedelta
import requests
import asyncio
import pandas as pd
import sys

# --- นำเข้าการตั้งค่า Telegram จาก config.py ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
except ImportError:
    TELEGRAM_BOT_TOKEN = None
    TELEGRAM_CHAT_ID = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PORTFOLIO_FILE = "my_portfolio.json"
HISTORY_FILE = "portfolio_history.json"

class ChatRequest(BaseModel):
    message: str

# 1. 🌟 ปลอมUser-Agent เพื่อไม่ให้ Yahoo บล็อก
def get_safe_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    })
    return session

# ==========================================
# 🚀 ระบบ Telegram Bot (ทำงานเบื้องหลัง)
# ==========================================
def send_telegram_msg(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

async def background_bot_task():
    print("🤖 Apex Telegram Bot Started! เชื่อมต่อหน้าเว็บและเฝ้าราคาหุ้นแล้วครับ...")
    alerted_today = []
    
    while True:
        try:
            if not os.path.exists(PORTFOLIO_FILE):
                await asyncio.sleep(300)
                continue
                
            with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                portfolio = json.load(f)
                
            tickers = list(set([p['ticker'].replace('.', '-') for p in portfolio]))
            if not tickers:
                await asyncio.sleep(300)
                continue

            raw_data = yf.download(tickers, period="1d", progress=False)
            df_c = raw_data['Close'] if 'Close' in raw_data else raw_data
            
            for p in portfolio:
                t = p['ticker']
                yf_t = t.replace('.', '-')
                alert_price = float(p.get('alert_price', 0))
                
                if alert_price > 0:
                    current_price = 0.0
                    if isinstance(df_c, pd.DataFrame) and yf_t in df_c.columns:
                        current_price = float(df_c[yf_t].dropna().iloc[-1])
                    elif isinstance(df_c, pd.Series) and df_c.name == yf_t:
                        current_price = float(df_c.dropna().iloc[-1])
                    
                    if 0 < current_price <= alert_price:
                        alert_id = f"{t}_{datetime.now().strftime('%Y-%m-%d')}"
                        if alert_id not in alerted_today:
                            msg = f"🚨 *Apex Price Alert!* 🚨\n\n📉 หุ้น: *{t}*\n💵 ราคาปัจจุบัน: *${current_price:.2f}*\n🎯 จุดแจ้งเตือน: ${alert_price:.2f}\n\nถึงแนวรับที่คุณตั้งไว้แล้วครับ!"
                            send_telegram_msg(msg)
                            alerted_today.append(alert_id)
        except Exception as e:
            print(f"Bot Error: {e}")
            
        await asyncio.sleep(300) # ตรวจสอบทุกๆ 5 นาที

@app.on_event("startup")
async def startup_event():
    # สั่งให้บอทรันทันทีที่เปิดเซิร์ฟเวอร์
    asyncio.create_task(background_bot_task())

# ==========================================
# 🌐 API Routes ของหน้าเว็บเดิม
# ==========================================
@app.get("/")
def check_status():
    return {"status": "ok", "message": "Apex Live Core Rework is running!"}

@app.get("/api/history")
def get_history():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/chart/{ticker}")
def get_candlestick_chart(ticker: str):
    try:
        # 🌟 ลบ get_safe_session() ออก แล้วให้ yf.download จัดการเอง
        chart_data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        
        if chart_data.empty: return []
        
        ohlc_list = []
        # จัด Format ข้อมูลให้ ApexCharts อ่านได้ (Timestamp, Open, High, Low, Close)
        for index, row in chart_data.iterrows():
            # ดักจับกรณี yfinance คืนค่ามาเป็น MultiIndex (เวอร์ชันใหม่)
            open_p = float(row['Open'].iloc[0]) if isinstance(row['Open'], pd.Series) else float(row['Open'])
            high_p = float(row['High'].iloc[0]) if isinstance(row['High'], pd.Series) else float(row['High'])
            low_p = float(row['Low'].iloc[0]) if isinstance(row['Low'], pd.Series) else float(row['Low'])
            close_p = float(row['Close'].iloc[0]) if isinstance(row['Close'], pd.Series) else float(row['Close'])

            ohlc_list.append({
                "x": int(index.timestamp() * 1000), # แปลงเป็น Epoch time
                "y": [round(open_p, 2), round(high_p, 2), round(low_p, 2), round(close_p, 2)]
            })
        return ohlc_list
    except Exception as e:
        print(f"Error fetching chart data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chart data")

@app.get("/api/portfolio")
def get_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        return {"status": "error", "message": "No portfolio file"}
    
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        portfolio = json.load(f)
        
    tickers = list(set([p['ticker'].replace('.', '-') for p in portfolio]))
    market_data = {}
    sparkline_data = {}
    
    if tickers:
        try:
            raw_data = yf.download(tickers, period="7d", progress=False)
            df_c = raw_data['Close'] if 'Close' in raw_data else raw_data
            for t in tickers:
                if isinstance(df_c, pd.DataFrame) and t in df_c.columns:
                    series = df_c[t].dropna()
                    market_data[t] = float(series.iloc[-1]) if not series.empty else 0.0
                    sparkline_data[t] = series.tolist()[-7:]
                elif isinstance(df_c, pd.Series) and df_c.name == t:
                    series = df_c.dropna()
                    market_data[t] = float(series.iloc[-1]) if not series.empty else 0.0
                    sparkline_data[t] = series.tolist()[-7:]
        except: pass

    total_val, total_cost = 0.0, 0.0
    assets = []
    
    for p in portfolio:
        t = p['ticker']
        yf_t = t.replace('.', '-')
        last_price = market_data.get(yf_t, float(p.get('last_price', 0.0)))
        shares = float(p.get('shares', 0))
        cost = float(p.get('cost', 0))
        
        val = last_price * shares
        total_cost_asset = cost * shares
        profit = val - total_cost_asset
        
        total_val += val
        total_cost += total_cost_asset
        
        # เช็คเทรนด์ (ราคาล่าสุดสูงกว่าราคาทุนหรือไม่)
        is_spark_up = last_price >= cost
        
        assets.append({
            "ticker": t, "shares": shares, "cost": cost, "alert_price": float(p.get('alert_price', 0)),
            "last_price": last_price, "value": val, "profit": profit, "group": p.get('group', 'Auto'),
            "sparkline": sparkline_data.get(yf_t, []), "is_spark_up": is_spark_up
        })

    # จำลองค่า Global Market (สามารถเขียนดึงจริงได้แบบ core.py)
    market = [
        {"name": "S&P 500", "value": 5000.25, "change": 1.2},
        {"name": "Nasdaq", "value": 16000.50, "change": -0.5},
        {"name": "Gold", "value": 2050.10, "change": 0.3}
    ]

    return {
        "summary": {
            "total_value": total_val, 
            "total_cost": total_cost,
            "profit": total_val - total_cost, 
            "profit_percent": ((total_val - total_cost) / total_cost * 100) if total_cost > 0 else 0
        },
        "market": market,
        "assets": assets
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)