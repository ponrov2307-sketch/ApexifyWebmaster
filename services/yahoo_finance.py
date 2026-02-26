import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from core.config import MARKET_INDICES

# 🌟 Core Fixes:
# 1. ลบ Session ออก (ให้ yfinance จัดการเอง)
# 2. แปลง pandas/numpy types เป็น python types (float, int, bool) เพื่อแก้ JSON Error

def get_market_summary():
    """ดึงข้อมูลดัชนีตลาดโลกไปโชว์ที่แถบบนสุด (Ticker)"""
    market_data = []
    
    try:
        tickers = list(MARKET_INDICES.keys())
        # ignore_tz=True ช่วยลดปัญหาเรื่อง Timezone ตีกัน
        data = yf.download(tickers, period="5d", interval="1d", progress=False, ignore_tz=True)
        
        for symbol, name in MARKET_INDICES.items():
            try:
                # ตรวจสอบว่ามีคอลัมน์นี้ไหม (รองรับ yfinance เวอร์ชันใหม่ที่โครงสร้างอาจเปลี่ยน)
                if symbol in data['Close'].columns:
                    series = data['Close'][symbol].dropna()
                else:
                    # กรณี Multi-level column (บางทีมันซ่อนอยู่ในระดับอื่น)
                    series = data.xs(symbol, level=1, axis=1)['Close'].dropna() if not data.empty else pd.Series()

                if len(series) >= 2:
                    # ⚠️ บังคับแปลงเป็น float เพื่อแก้ Error: Series is not JSON serializable
                    current = float(series.iloc[-1])
                    prev = float(series.iloc[-2])
                    change_pct = ((current - prev) / prev) * 100
                    
                    val_str = f"{current:.2f}" if symbol == "THB=X" else f"{current:,.2f}"
                    
                    market_data.append({
                        "name": name,
                        "value": val_str,
                        "change": round(float(change_pct), 2),
                        "is_up": bool(change_pct >= 0) # แปลง numpy.bool เป็น python bool
                    })
                else:
                    market_data.append({"name": name, "value": "N/A", "change": 0.0, "is_up": True})
            except Exception:
                # ถ้าดึงตัวไหนพลาด ให้ข้ามไปแล้วใส่ N/A แทนที่จะพังทั้งเว็บ
                market_data.append({"name": name, "value": "N/A", "change": 0.0, "is_up": True})
                
    except Exception as e:
        print(f"❌ Market Data Error: {e}")
        # ข้อมูลสำรอง
        for name in MARKET_INDICES.values():
             market_data.append({"name": name, "value": "Offline", "change": 0.0, "is_up": True})
             
    return market_data

def get_live_price(ticker: str):
    """ดึงราคาล่าสุดของหุ้น 1 ตัว"""
    try:
        stock = yf.Ticker(ticker)
        # fast_info มักจะคืนค่าเป็น float อยู่แล้ว แต่แปลงซ้ำเพื่อความชัวร์
        price = stock.fast_info.last_price
        return float(price) if price else 0.0
    except Exception:
        # Fallback: ถ้า fast_info พัง ลองดึงจาก history 1 วัน
        try:
            data = yf.download(ticker, period="1d", progress=False, ignore_tz=True)
            if not data.empty and 'Close' in data:
                return float(data['Close'].iloc[-1])
        except:
            pass
        return 0.0

def get_sparkline_data(ticker: str, days: int = 7):
    """ดึงข้อมูลไปวาดกราฟเส้นจิ๋ว"""
    try:
        data = yf.download(ticker, period=f"{days}d", interval="1d", progress=False, ignore_tz=True)
        if data.empty: return [], True
        
        # แปลงเป็น list ปกติ
        closes = data['Close'].dropna().tolist()
        opens = data['Open'].dropna().tolist()
        
        # แก้ปัญหา JSON Error ถ้าข้อมูลข้างในยังเป็น numpy type
        closes = [float(x) for x in closes]
        
        is_up = True
        if closes and opens:
            # แปลงเป็น bool ปกติ
            is_up = bool(closes[-1] >= float(opens[0]))
            
        return closes, is_up
    except:
        return [], True

def get_candlestick_data(ticker: str, period: str = "1mo"):
    """ดึงข้อมูล OHLC ไปวาดกราฟแท่งเทียนชุดใหญ่"""
    try:
        data = yf.download(ticker, period=period, interval="1d", progress=False, ignore_tz=True)
        if data.empty: return []
        
        # 🌟 จัดการปัญหา MultiIndex ของ yfinance เวอร์ชั่นใหม่
        if isinstance(data.columns, pd.MultiIndex):
            # ยุบตารางให้เหลือแค่ชั้นเดียว ป้องกัน Error Series
            data = data.xs(ticker, level=1, axis=1)
            
        ohlc = []
        for index, row in data.iterrows():
            # 🌟 ใช้ท่าที่ Pandas แนะนำเพื่อดึงตัวเลขออกมา (เช็คว่าเป็น Series ไหม)
            open_val = row['Open'].iloc[0] if hasattr(row['Open'], 'iloc') else row['Open']
            high_val = row['High'].iloc[0] if hasattr(row['High'], 'iloc') else row['High']
            low_val = row['Low'].iloc[0] if hasattr(row['Low'], 'iloc') else row['Low']
            close_val = row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close']
            
            ohlc.append({
                "date": index.strftime('%Y-%m-%d'),
                "open": float(open_val),
                "high": float(high_val),
                "low": float(low_val),
                "close": float(close_val)
            })
        return ohlc
    except Exception as e:
        print(f"❌ Chart Error for {ticker}: {e}")
        return []