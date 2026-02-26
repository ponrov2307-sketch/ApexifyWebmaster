from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import yfinance as yf
from datetime import datetime, timedelta
import requests

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

@app.get("/")
def check_status():
    return {"status": "ok", "message": "Apex Live Core Rework is running!"}

@app.get("/api/portfolio")
def get_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        return {"status": "error", "message": "No portfolio file"}
    
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # รวบรวมรายชื่อหุ้น
    tickers_list = list(set([item['ticker'] for item in data]))
    
    # 🌟 ดึงข้อมูลดัชนีตลาด S&P500, NASDAQ, ทอง, บาท
    indices_map = {"^GSPC": "S&P 500", "^IXIC": "NASDAQ", "GC=F": "GOLD", "THB=X": "USD/THB"}
    all_symbols = tickers_list + list(indices_map.keys())

    # 2. 🌟 ดึงข้อมูลย้อนหลัง 7 วันเพื่อทำ Sparkline (OHLC เพื่อเอา Open/Close มาเช็คสี)
    try:
        session = get_safe_session()
        yf_data = yf.download(all_symbols, period="7d", interval="1d", progress=False, session=session)
    except Exception as e:
        print(f"Error downloading data: {e}")
        yf_data = None

    total_cost = 0
    total_value = 0
    allocation = {}
    
    processed_assets = []
    
    for item in data:
        ticker = item['ticker']
        cost = item['cost'] * item['shares']
        
        if yf_data is not None and ticker in yf_data['Close']:
            # ดึงราคาปิด 7 วันล่าสุด (dropna เพื่อความปลอดภัย)
            closes = yf_data['Close'][ticker].dropna().tolist()
            opens = yf_data['Open'][ticker].dropna().tolist()
            
            if closes:
                current_price = closes[-1]
                # 🌟 สร้างข้อมูล Sparkline (Close prices)
                item['sparkline'] = closes
                # 🌟 เช็คสีของ Sparkline: ราคาเปิดวันแรก เทียบกับ ราคาปิดวันสุดท้าย
                item['is_spark_up'] = current_price >= opens[0]
            else:
                current_price = item.get('last_price', item['cost'])
                item['sparkline'] = [current_price] * 7
                item['is_spark_up'] = True
        else:
            current_price = item.get('last_price', item['cost'])
            item['sparkline'] = [current_price] * 7
            item['is_spark_up'] = True
            
        item['last_price'] = current_price
        value = current_price * item['shares']
        
        total_cost += cost
        total_value += value
        
        grp = item.get('group', 'Other')
        allocation[grp] = allocation.get(grp, 0) + value
        processed_assets.append(item)

    profit = total_value - total_cost
    
    # 🌟 ข้อมูลดัชนีตลาด
    market_indices = []
    for symbol, name in indices_map.items():
        if yf_data is not None and symbol in yf_data['Close']:
            closes = yf_data['Close'][symbol].dropna().tolist()
            if len(closes) >= 2:
                current = closes[-1]
                prev = closes[-2]
                change_pct = ((current - prev) / prev) * 100
                val_str = f"{current:.2f}" if symbol == "THB=X" else f"{current:,.2f}"
                market_indices.append({"name": name, "value": val_str, "change": round(change_pct, 2)})
        else:
            market_indices.append({"name": name, "value": "N/A", "change": 0})
    
    return {
        "summary": {
            "total_cost": total_cost,
            "total_value": total_value,
            "profit": profit,
            "profit_percent": (profit/total_cost)*100 if total_cost > 0 else 0
        },
        "allocation": allocation,
        "assets": processed_assets,
        "market": market_indices
    }

# 🌟 API ใหม่: ดึงข้อมูลกราฟเทียน (OHLC) รายตัว
@app.get("/api/chart/{ticker}")
def get_candlestick_chart(ticker: str):
    try:
        session = get_safe_session()
        # ดึงประวัติ 1 เดือน กราฟรายวัน
        chart_data = yf.download(ticker, period="1mo", interval="1d", progress=False, session=session)
        
        if chart_data.empty: return []
        
        ohlc_list = []
        # จัด Format ข้อมูลให้ ApexCharts อ่านได้ (Timestamp, Open, High, Low, Close)
        for index, row in chart_data.iterrows():
            ohlc_list.append({
                "x": int(index.timestamp() * 1000), # แปลงเป็น Epoch time
                "y": [round(row['Open'], 2), round(row['High'], 2), round(row['Low'], 2), round(row['Close'], 2)]
            })
        return ohlc_list
    except Exception as e:
        print(f"Error fetching chart data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chart data")

@app.get("/api/history")
def get_history():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# API รับคำสั่ง CRUD เพิ่ม/ลบ (ยังไม่เขียน Logic บันทึกไฟล์ เพื่อความรวดเร็ว)
@app.post("/api/portfolio")
def add_stock(stock: dict): return {"status": "ok", "message": f"Added {stock['ticker']} (Stub)"}

@app.post("/api/chat")
def chat_ai(req: ChatRequest):
    return {"reply": f"AI ได้รับข้อความ: {req.message} (ฟังก์ชัน Gemini จะเปิดใช้งานภายหลังDeploy)"}