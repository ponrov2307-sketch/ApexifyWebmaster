from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import yfinance as yf
import pandas as pd
import asyncio
import requests
from datetime import datetime
import sys

# ชี้ Path กลับไปที่โฟลเดอร์หลักเพื่ออ่าน my_portfolio.json
PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "..", "my_portfolio.json")

# ==========================================
# ⚙️ ตั้งค่า Telegram Bot
# ==========================================
TELEGRAM_BOT_TOKEN = "ใส่_TOKEN_บอทของคุณที่นี่"
TELEGRAM_CHAT_ID = "ใส่_CHAT_ID_ของคุณที่นี่"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AssetData(BaseModel):
    ticker: str
    shares: float
    cost: float
    alert_price: float
    group: str

# ==========================================
# 💾 ฟังก์ชันจัดการข้อมูล
# ==========================================
def load_data():
    if not os.path.exists(PORTFOLIO_FILE): return []
    try:
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

def save_data(data):
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ==========================================
# 🚀 Telegram Bot (เฝ้าราคาหุ้นเบื้องหลัง)
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
    print("🤖 Apex Telegram Bot Started...")
    alerted_today = []
    
    while True:
        try:
            portfolio = load_data()
            if not portfolio:
                await asyncio.sleep(300)
                continue
                
            tickers = list(set([p['ticker'] for p in portfolio]))
            raw_data = yf.download(tickers, period="1d", progress=False)
            df_c = raw_data['Close'] if 'Close' in raw_data else raw_data
            
            for p in portfolio:
                t = p['ticker']
                alert_price = float(p.get('alert_price', 0))
                if alert_price > 0:
                    current_price = 0.0
                    if isinstance(df_c, pd.DataFrame) and t in df_c.columns:
                        current_price = float(df_c[t].dropna().iloc[-1])
                    elif isinstance(df_c, pd.Series) and df_c.name == t:
                        current_price = float(df_c.dropna().iloc[-1])
                    
                    # ถ้าราคาลงมาถึงจุดตั้งเตือน
                    if 0 < current_price <= alert_price:
                        alert_id = f"{t}_{datetime.now().strftime('%Y-%m-%d')}"
                        if alert_id not in alerted_today:
                            msg = f"🚨 *Apex Price Alert!* 🚨\n\n📉 หุ้น: *{t}*\n💵 ราคาปัจจุบัน: *${current_price:.2f}*\n🎯 จุดแจ้งเตือน: ${alert_price:.2f}\n\nถึงแนวรับที่คุณตั้งไว้แล้วครับ!"
                            send_telegram_msg(msg)
                            alerted_today.append(alert_id)
        except Exception as e:
            print(f"Bot Error: {e}")
            
        await asyncio.sleep(300) # บอทเช็คราคาทุก 5 นาที

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_bot_task())

# ==========================================
# 🌐 Web API
# ==========================================
@app.get("/api/dashboard")
def get_dashboard():
    portfolio = load_data()
    tickers = list(set([p['ticker'] for p in portfolio]))
    market_data = {}
    
    if tickers:
        try:
            raw_data = yf.download(tickers, period="1d", progress=False)
            df_c = raw_data['Close'] if 'Close' in raw_data else raw_data
            for t in tickers:
                if isinstance(df_c, pd.DataFrame) and t in df_c.columns:
                    market_data[t] = float(df_c[t].dropna().iloc[-1])
                elif isinstance(df_c, pd.Series) and df_c.name == t:
                    market_data[t] = float(df_c.dropna().iloc[-1])
        except: pass

    total_val, total_cost = 0.0, 0.0
    assets = []
    
    for p in portfolio:
        t = p['ticker']
        last_price = market_data.get(t, float(p.get('last_price', 0.0)))
        shares = float(p.get('shares', 0))
        cost = float(p.get('cost', 0))
        
        val = last_price * shares
        total_cost_asset = cost * shares
        profit = val - total_cost_asset
        profit_pct = (profit / total_cost_asset * 100) if total_cost_asset > 0 else 0
        
        total_val += val
        total_cost += total_cost_asset
        
        assets.append({
            "ticker": t, "shares": shares, "cost": cost, "alert_price": float(p.get('alert_price', 0)),
            "last_price": last_price, "value": val, "profit": profit, "profit_pct": profit_pct, "group": p.get('group', 'Auto')
        })

    return {
        "summary": {
            "net_worth": total_val, 
            "total_profit": total_val - total_cost, 
            "total_profit_pct": ((total_val - total_cost) / total_cost * 100) if total_cost > 0 else 0
        },
        "assets": sorted(assets, key=lambda x: x['value'], reverse=True)
    }

@app.post("/api/asset")
def save_asset(data: AssetData):
    portfolio = load_data()
    found = False
    for p in portfolio:
        if p['ticker'] == data.ticker:
            p.update(data.dict())
            found = True
            break
    if not found:
        new_asset = data.dict()
        new_asset['last_price'] = 0.0
        portfolio.append(new_asset)
    save_data(portfolio)
    return {"status": "success"}

@app.delete("/api/asset/{ticker}")
def delete_asset(ticker: str):
    portfolio = [p for p in load_data() if p['ticker'] != ticker]
    save_data(portfolio)
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)