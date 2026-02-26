from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import yfinance as yf
from datetime import datetime
import requests
import asyncio
import pandas as pd
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
except ImportError:
    TELEGRAM_BOT_TOKEN = None
    TELEGRAM_CHAT_ID = None

# นำเข้า core.py เพื่อใช้ฟังก์ชันส่ง Morning Report
import core 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PORTFOLIO_FILE = "my_portfolio.json"
HISTORY_FILE = "portfolio_history.json"
LAST_REPORT_FILE = "last_report_date.txt"

class ChatRequest(BaseModel):
    message: str

class AssetData(BaseModel):
    ticker: str
    shares: float
    cost: float
    alert_price: float
    group: str

# ==========================================
# 🚀 ระบบ Telegram Bot & Auto Save (ทำงานเบื้องหลังตลอดเวลา)
# ==========================================
def send_telegram_msg(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except: pass

async def background_bot_task():
    print("🤖 Apex Telegram Bot Started! เฝ้าราคาและเตรียมส่ง Morning Report...")
    alerted_today = []
    
    while True:
        try:
            if not os.path.exists(PORTFOLIO_FILE):
                await asyncio.sleep(60)
                continue
                
            with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                portfolio = json.load(f)
                
            tickers = list(set([p['ticker'].replace('.', '-') for p in portfolio]))
            if not tickers:
                await asyncio.sleep(60)
                continue

            # 🌟 [ดึงราคาสดๆ เพื่อเช็ค Alert]
            market_data = {}
            for t in tickers:
                try:
                    df = yf.download(t, period="1d", progress=False)
                    if not df.empty:
                        close_price = float(df['Close'].iloc[-1])
                        market_data[t] = close_price
                except: pass
            
            # 🌟 1. ระบบแจ้งเตือนราคา (Price Alert)
            for p in portfolio:
                t = p['ticker']
                yf_t = t.replace('.', '-')
                alert_price = float(p.get('alert_price', 0))
                current_price = market_data.get(yf_t, 0.0)
                
                if alert_price > 0 and 0 < current_price <= alert_price:
                    alert_id = f"{t}_{datetime.now().strftime('%Y-%m-%d')}"
                    if alert_id not in alerted_today:
                        msg = f"🚨 *Apex Price Alert!* 🚨\n\n📉 หุ้น: *{t}*\n💵 ราคาปัจจุบัน: *${current_price:.2f}*\n🎯 จุดแจ้งเตือน: ${alert_price:.2f}\n\nถึงจุดที่คุณตั้งเตือนไว้แล้ว!"
                        send_telegram_msg(msg)
                        alerted_today.append(alert_id)

            # 🌟 2. ระบบ Morning Report (ส่งสรุปยอดตอนตี 5 เหมือน auto_save.py)
            now = datetime.now()
            if now.hour >= 5:
                today_str = now.strftime("%Y-%m-%d")
                last_sent = ""
                if os.path.exists(LAST_REPORT_FILE):
                    with open(LAST_REPORT_FILE, "r") as f: last_sent = f.read().strip()
                
                if last_sent != today_str:
                    print("📬 Sending Morning Report to Telegram...")
                    indices = {"^GSPC": 0, "^IXIC": 0, "GC=F": 0, "THB=X": 0}
                    try:
                        for idx in indices.keys():
                            df_idx = yf.download(idx, period="1d", progress=False)
                            if not df_idx.empty:
                                indices[idx] = float(df_idx['Close'].iloc[-1])
                    except: pass
                    
                    core.send_daily_report(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, portfolio, market_data, indices, HISTORY_FILE)
                    with open(LAST_REPORT_FILE, "w") as f: f.write(today_str)

        except Exception as e:
            print(f"Bot Error: {e}")
            
        await asyncio.sleep(60) # อัพเดทและเช็คทุกๆ 60 วินาที

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_bot_task())

# ==========================================
# 🌐 API Routes สำหรับหน้าเว็บ Dashboard
# ==========================================
@app.get("/api/portfolio")
def get_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        return {"status": "error", "message": "No portfolio file"}
    
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        portfolio = json.load(f)
        
    tickers = list(set([p['ticker'].replace('.', '-') for p in portfolio]))
    market_data = {}
    sparkline_data = {}
    
    # 🌟 [แก้ไขวิธีดึงข้อมูลป้องกัน Yahoo Block กราฟ Sparkline จะกลับมาตรงนี้]
    for t in tickers:
        try:
            df = yf.download(t, period="7d", progress=False)
            if not df.empty:
                prices = df['Close'].dropna().tolist()
                # ตรวจสอบการซ้อนทับของข้อมูล (MultiIndex)
                if isinstance(prices[0], pd.Series):
                    prices = [float(p.iloc[0]) for p in prices]
                else:
                    prices = [float(p) for p in prices]
                
                if prices:
                    market_data[t] = prices[-1]
                    sparkline_data[t] = prices[-7:]
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
        
        is_spark_up = last_price >= cost
        
        assets.append({
            "ticker": t, "shares": shares, "cost": cost, "alert_price": float(p.get('alert_price', 0)),
            "last_price": last_price, "value": val, "profit": profit, "group": p.get('group', 'Auto'),
            "sparkline": sparkline_data.get(yf_t, []), "is_spark_up": is_spark_up
        })

    # อัพเดท Market Indices ด้านบนแบบเรียลไทม์
    market_indices = []
    indices_dict = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq", "GC=F": "Gold", "THB=X": "THB"}
    for sym, name in indices_dict.items():
        try:
            df_m = yf.download(sym, period="2d", progress=False)
            if len(df_m) >= 2:
                curr = float(df_m['Close'].iloc[-1])
                prev = float(df_m['Close'].iloc[-2])
                pct = ((curr - prev) / prev) * 100
                market_indices.append({"name": name, "value": round(curr, 2), "change": round(pct, 2)})
        except: pass

    return {
        "summary": {
            "total_value": total_val, 
            "total_cost": total_cost,
            "profit": total_val - total_cost, 
            "profit_percent": ((total_val - total_cost) / total_cost * 100) if total_cost > 0 else 0
        },
        "market": market_indices,
        "assets": assets
    }

@app.get("/api/history")
def get_history():
    if not os.path.exists(HISTORY_FILE): return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

@app.get("/api/chart/{ticker}")
def get_candlestick_chart(ticker: str):
    try:
        chart_data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if chart_data.empty: return []
        ohlc_list = []
        for index, row in chart_data.iterrows():
            o = float(row['Open'].iloc[0]) if isinstance(row['Open'], pd.Series) else float(row['Open'])
            h = float(row['High'].iloc[0]) if isinstance(row['High'], pd.Series) else float(row['High'])
            l = float(row['Low'].iloc[0]) if isinstance(row['Low'], pd.Series) else float(row['Low'])
            c = float(row['Close'].iloc[0]) if isinstance(row['Close'], pd.Series) else float(row['Close'])
            ohlc_list.append({"x": int(index.timestamp() * 1000), "y": [round(o, 2), round(h, 2), round(l, 2), round(c, 2)]})
        return ohlc_list
    except:
        raise HTTPException(status_code=500, detail="Failed to fetch chart")

@app.post("/api/asset")
def save_asset(data: AssetData):
    portfolio = []
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f: portfolio = json.load(f)
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
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f: json.dump(portfolio, f, indent=4)
    return {"status": "success"}

@app.delete("/api/asset/{ticker}")
def delete_asset(ticker: str):
    portfolio = []
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f: portfolio = json.load(f)
    portfolio = [p for p in portfolio if p['ticker'] != ticker]
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f: json.dump(portfolio, f, indent=4)
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)