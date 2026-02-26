import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
from core.config import MARKET_INDICES

# 🌟 ท่าไม้ตายปลอมตัวเป็นคน (Anti-Block)
def get_safe_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    })
    return session

def get_market_summary():
    """ดึงข้อมูลดัชนีตลาดโลกไปโชว์ที่แถบบนสุด (Ticker)"""
    session = get_safe_session()
    market_data = []
    
    try:
        # ใช้ session เพื่อป้องกันการโดนบล็อก
        tickers = list(MARKET_INDICES.keys())
        data = yf.download(tickers, period="5d", interval="1d", progress=False, session=session)
        
        for symbol, name in MARKET_INDICES.items():
            if symbol in data['Close'] and not data['Close'][symbol].empty:
                # ดึงข้อมูล 2 วันล่าสุดที่ไม่มีค่าว่าง (dropna)
                closes = data['Close'][symbol].dropna()
                if len(closes) >= 2:
                    current = closes.iloc[-1]
                    prev = closes.iloc[-2]
                    change_pct = ((current - prev) / prev) * 100
                    
                    # รูปแบบตัวเลข (ถ้าเป็นค่าเงินบาทใช้ทศนิยม 2 ตำแหน่งปกติ)
                    val_str = f"{current:.2f}" if symbol == "THB=X" else f"{current:,.2f}"
                    
                    market_data.append({
                        "name": name,
                        "value": val_str,
                        "change": round(change_pct, 2),
                        "is_up": change_pct >= 0
                    })
                else:
                    market_data.append({"name": name, "value": "N/A", "change": 0.0, "is_up": True})
            else:
                market_data.append({"name": name, "value": "Error", "change": 0.0, "is_up": True})
                
    except Exception as e:
        print(f"❌ Error fetching market data: {e}")
        # ข้อมูลสำรองกันเว็บพัง
        for name in MARKET_INDICES.values():
             market_data.append({"name": name, "value": "N/A", "change": 0.0, "is_up": True})
             
    return market_data

def get_live_price(ticker: str):
    """ดึงราคาล่าสุดของหุ้น 1 ตัว"""
    try:
        session = get_safe_session()
        stock = yf.Ticker(ticker, session=session)
        # ใช้ fast_info จะเร็วกว่าการโหลด history ทั้งหมด
        return stock.fast_info['last_price']
    except Exception:
        return 0.0

def get_sparkline_data(ticker: str, days: int = 7):
    """ดึงข้อมูลไปวาดกราฟเส้นจิ๋ว (Sparkline) ในตาราง"""
    try:
        session = get_safe_session()
        data = yf.download(ticker, period=f"{days}d", interval="1d", progress=False, session=session)
        if data.empty: return [], True
        
        closes = data['Close'].dropna().tolist()
        opens = data['Open'].dropna().tolist()
        
        # เช็คว่าราคาเปิดวันแรก น้อยกว่าหรือเท่ากับ ราคาปิดวันสุดท้ายหรือไม่ (เพื่อทำสีเขียว/แดง)
        is_up = True
        if closes and opens:
            is_up = closes[-1] >= opens[0]
            
        return closes, is_up
    except:
        return [], True

def get_candlestick_data(ticker: str, period: str = "1mo"):
    """ดึงข้อมูล OHLC ไปวาดกราฟแท่งเทียนชุดใหญ่"""
    try:
        session = get_safe_session()
        data = yf.download(ticker, period=period, interval="1d", progress=False, session=session)
        if data.empty: return []
        
        # แปลงข้อมูลให้อยู่ในรูปแบบที่หน้าเว็บ (Plotly/Highcharts) ชอบ
        ohlc = []
        for index, row in data.iterrows():
            ohlc.append({
                "date": index.strftime('%Y-%m-%d'),
                "open": round(row['Open'], 2),
                "high": round(row['High'], 2),
                "low": round(row['Low'], 2),
                "close": round(row['Close'], 2)
            })
        return ohlc
    except Exception as e:
        print(f"❌ Error fetching candlestick for {ticker}: {e}")
        return []