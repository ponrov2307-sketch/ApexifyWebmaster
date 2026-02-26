from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import sys
import yfinance as yf
import pandas as pd
from datetime import datetime
import threading

# นำเข้าโมดูลจากโฟลเดอร์หลัก (Root Directory)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import core
from config import *
import google.generativeai as genai

# ตั้งค่า Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PORTFOLIO_FILE = "../my_portfolio.json"
HISTORY_FILE = "../portfolio_history.json"

class AssetData(BaseModel):
    ticker: str
    shares: float
    cost: float
    alert_price: float
    group: str

class ChatMessage(BaseModel):
    message: str

def load_data(filepath):
    if not os.path.exists(filepath): return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

def save_data(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

@app.get("/api/dashboard")
def get_dashboard_data():
    portfolio = load_data(PORTFOLIO_FILE)
    tickers = list(set([p['ticker'].replace('.', '-') for p in portfolio]))
    
    market_data = {}
    market_indices_data = {}
    indices = {"^GSPC": "🇺🇸 S&P 500", "^IXIC": "💻 Nasdaq", "GC=F": "🥇 Gold", "THB=X": "🇹🇭 THB"}
    
    try:
        # ดึงราคาหุ้น
        if tickers:
            raw_data = yf.download(tickers, period="1d", progress=False)
            df_c = raw_data['Close'] if 'Close' in raw_data else raw_data
            for t in tickers:
                if isinstance(df_c, pd.DataFrame) and t in df_c.columns:
                    market_data[t] = float(df_c[t].dropna().iloc[-1])
                elif isinstance(df_c, pd.Series) and df_c.name == t:
                    market_data[t] = float(df_c.dropna().iloc[-1])
        
        # ดึงราคาดัชนีตลาด
        idx_data = yf.download(list(indices.keys()), period="1d", progress=False)
        idx_c = idx_data['Close'] if 'Close' in idx_data else idx_data
        for k, v in indices.items():
            val = 0.0
            if isinstance(idx_c, pd.DataFrame) and k in idx_c.columns:
                val = float(idx_c[k].dropna().iloc[-1])
            elif isinstance(idx_c, pd.Series) and idx_c.name == k:
                val = float(idx_c.dropna().iloc[-1])
            market_indices_data[v] = val
    except:
        pass

    total_val = 0.0
    total_cost = 0.0
    assets = []
    
    for p in portfolio:
        t = p['ticker'].replace('.', '-')
        last_price = market_data.get(t, p.get('last_price', 0.0))
        p['last_price'] = last_price # อัพเดทราคาล่าสุดกลับเข้าข้อมูล
        shares = float(p.get('shares', 0))
        cost_per_share = float(p.get('cost', 0))
        
        val = last_price * shares
        cost = cost_per_share * shares
        profit = val - cost
        profit_pct = (profit / cost * 100) if cost > 0 else 0
        
        total_val += val
        total_cost += cost
        
        assets.append({
            "ticker": p['ticker'],
            "shares": shares,
            "cost": cost_per_share,
            "alert_price": float(p.get('alert_price', 0)),
            "last_price": last_price,
            "value": val,
            "profit": profit,
            "profit_pct": profit_pct,
            "group": p.get('group', 'Auto')
        })
        
    save_data(PORTFOLIO_FILE, portfolio) # บันทึกราคาล่าสุดลงไฟล์
        
    total_profit = total_val - total_cost
    total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0

    return {
        "summary": {
            "net_worth": total_val,
            "total_cost": total_cost,
            "total_profit": total_profit,
            "total_profit_pct": total_profit_pct
        },
        "indices": market_indices_data,
        "assets": sorted(assets, key=lambda x: x['value'], reverse=True)
    }

@app.post("/api/asset")
def save_asset(data: AssetData):
    portfolio = load_data(PORTFOLIO_FILE)
    # ค้นหาว่ามีหุ้นนี้อยู่แล้วหรือไม่
    found = False
    for p in portfolio:
        if p['ticker'] == data.ticker:
            p['shares'] = data.shares
            p['cost'] = data.cost
            p['alert_price'] = data.alert_price
            p['group'] = data.group
            found = True
            break
    if not found:
        portfolio.append({
            "ticker": data.ticker,
            "shares": data.shares,
            "cost": data.cost,
            "alert_price": data.alert_price,
            "last_price": 0.0,
            "group": data.group
        })
    save_data(PORTFOLIO_FILE, portfolio)
    return {"status": "success"}

@app.delete("/api/asset/{ticker}")
def delete_asset(ticker: str):
    portfolio = load_data(PORTFOLIO_FILE)
    portfolio = [p for p in portfolio if p['ticker'] != ticker]
    save_data(PORTFOLIO_FILE, portfolio)
    return {"status": "success"}

@app.post("/api/telegram")
def trigger_telegram():
    portfolio = load_data(PORTFOLIO_FILE)
    prices = {p['ticker']: p.get('last_price', 0) for p in portfolio}
    indices = {"^GSPC": 0, "^IXIC": 0, "GC=F": 0, "THB=X": 0}
    
    def run_report():
        core.send_daily_report(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, portfolio, prices, indices, HISTORY_FILE)
        
    threading.Thread(target=run_report).start()
    return {"status": "Report sending initiated"}

@app.post("/api/ai")
def ai_chat(chat: ChatMessage):
    if not GEMINI_API_KEY:
        return {"reply": "❌ ยังไม่ได้ตั้งค่า GEMINI_API_KEY ใน config.py"}
    
    portfolio = load_data(PORTFOLIO_FILE)
    port_data = [f"{p['ticker']} ({p['group']}): {p['shares']} shares @ ${p['cost']}" for p in portfolio]
    system_prompt = f"คุณคือ Apex AI ผู้เชี่ยวชาญการลงทุน ข้อมูลพอร์ตปัจจุบัน: {', '.join(port_data)}\\nโปรดตอบคำถามสั้นๆ กระชับ เป็นภาษาไทย: {chat.message}"
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(system_prompt)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"❌ Error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)