import yfinance as yf
import pandas as pd
from datetime import datetime
from core.config import MARKET_INDICES

# 🌟 พื้นที่จดจำราคาหุ้นส่วนกลาง (Global Cache)
GLOBAL_PRICE_CACHE = {}
GLOBAL_SPARKLINE_CACHE = {}

def update_global_cache_batch(tickers: list):
    """🌟 อัปเดตราคาแบบ Intraday (ทุก 5-15 นาที) เพื่อกราฟ Sparkline ที่ขยับจริง"""
    if not tickers: return
    try:
        # ดึง 5 วันย้อนหลัง กราฟแท่งละ 15 นาที (ทำให้ Sparkline ขยับระหว่างวัน)
        data = yf.download(tickers, period="5d", interval="15m", progress=False, ignore_tz=True)
        if data.empty: return
        for ticker in tickers:
            try:
                if len(tickers) > 1 and isinstance(data.columns, pd.MultiIndex):
                    series = data['Close'][ticker].dropna()
                else:
                    series = data['Close'].dropna()
                    
                if len(series) > 0:
                    closes = [float(c) for c in series.tolist()]
                    GLOBAL_PRICE_CACHE[ticker] = closes[-1] 
                    GLOBAL_SPARKLINE_CACHE[ticker] = closes[-40:] # เอาแค่ 40 แท่งล่าสุดให้เส้นสวยๆ
            except Exception: pass
    except Exception as e:
        print(f"⚠️ Global Cache Update Error: {e}")

def get_market_summary():
    market_data = []
    try:
        tickers = list(MARKET_INDICES.keys())
        data = yf.download(tickers, period="5d", interval="1d", progress=False, ignore_tz=True)
        for symbol, name in MARKET_INDICES.items():
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    series = data['Close'][symbol].dropna()
                else:
                    series = data['Close'].dropna()
                if len(series) >= 2:
                    current, prev = float(series.iloc[-1]), float(series.iloc[-2])
                    change = current - prev
                    market_data.append({'name': name, 'value': f"{current:,.2f}", 'change': f"{abs(change):,.2f}", 'is_up': change >= 0})
            except: pass
    except: pass
    return market_data

def get_live_price(ticker: str) -> float:
    if ticker in GLOBAL_PRICE_CACHE:
        return GLOBAL_PRICE_CACHE[ticker]
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if data.empty: return 0.0
        if isinstance(data.columns, pd.MultiIndex):
            price = float(data['Close'][ticker].dropna().iloc[-1])
        else:
            price = float(data['Close'].dropna().iloc[-1])
        GLOBAL_PRICE_CACHE[ticker] = price
        return price
    except: return 0.0

def get_sparkline_data(ticker: str, days: int = 7):
    closes = GLOBAL_SPARKLINE_CACHE.get(ticker, [])
    if not closes:
        try:
            data = yf.download(ticker, period=f"{days}d", interval="1d", progress=False)
            if not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    closes = data['Close'][ticker].dropna().tolist()
                else:
                    closes = data['Close'].dropna().tolist()
                closes = [float(c) for c in closes]
                GLOBAL_SPARKLINE_CACHE[ticker] = closes
        except:
            return [], True
    is_up = closes[-1] >= closes[0] if len(closes) > 1 else True
    return closes, is_up

def get_candlestick_data(ticker: str, period: str = "3mo"):
    try:
        data = yf.download(ticker, period=period, interval="1d", progress=False)
        if data.empty: return []
        if isinstance(data.columns, pd.MultiIndex):
            data = data.xs(ticker, level=1, axis=1)
        ohlc = []
        for index, row in data.iterrows():
            ohlc.append({"date": index.strftime('%Y-%m-%d'), "open": float(row['Open']), "high": float(row['High']), "low": float(row['Low']), "close": float(row['Close']), "volume": int(row['Volume'])})
        return ohlc
    except: return []

def get_sp500_ytd():
    try:
        data = yf.download('VOO', period="ytd", interval="1mo", progress=False)
        if data.empty: return ['Jan'], [0]
        if isinstance(data.columns, pd.MultiIndex):
            closes = data['Close']['VOO'].dropna().tolist()
        else:
            closes = data['Close'].dropna().tolist()
        base = closes[0] 
        returns = [round(((c - base) / base) * 100, 2) for c in closes]
        months = data.index.strftime('%b').tolist()
        return months, returns
    except: return ['Jan'], [0]

def get_real_dividend_data(tickers: list):
    dividend_items = {}
    try:
        for ticker in tickers:
            t = yf.Ticker(ticker)
            info = t.info
            yield_pct = info.get('dividendYield', 0)
            yield_pct = (yield_pct * 100) if yield_pct else 0
            
            ex_date_ts = info.get('exDividendDate')
            ex_date = datetime.fromtimestamp(ex_date_ts).strftime('%Y-%m-%d') if ex_date_ts else 'N/A'
            
            dividend_items[ticker] = {
                'yield': yield_pct,
                'ex_date': ex_date,
                'amount_per_share': info.get('dividendRate', 0) or 0
            }
    except Exception as e:
        print(f"Dividend API Error: {e}")
    return dividend_items

def get_portfolio_historical_growth(portfolio_items: list):
    if not portfolio_items: return ['Mon'], [0]
    tickers = [item['ticker'] for item in portfolio_items]
    try:
        data = yf.download(tickers, period="1mo", interval="1d", progress=False)
        if data.empty: return ['Mon'], [0]
        
        dates = data.index.strftime('%b %d').tolist()
        total_values = [0] * len(dates)
        
        for item in portfolio_items:
            t = item['ticker']
            shares = item['shares']
            if len(tickers) > 1 and isinstance(data.columns, pd.MultiIndex):
                series = data['Close'][t].ffill().fillna(0).tolist()
            else:
                series = data['Close'].ffill().fillna(0).tolist()
            
            for i, val in enumerate(series):
                if i < len(total_values):
                    total_values[i] += float(val) * shares
                    
        return dates, total_values
    except:
        return ['Mon'], [0]

def get_advanced_stock_info(tickers: list):
    """ดึงข้อมูล Sector และ Target Price ของจริงจาก Yahoo Finance"""
    info_dict = {}
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            info_dict[ticker] = {
                'sector': info.get('sector', 'Unknown'),
                'target_price': info.get('targetMeanPrice', 0),
                'beta': info.get('beta', 1.0)
            }
        except:
            info_dict[ticker] = {'sector': 'Unknown', 'target_price': 0, 'beta': 1.0}
    return info_dict

def calculate_rsi_from_prices(prices, period=14):
    """คำนวณ RSI ของจริงจากลิสต์ราคาปิด"""
    if len(prices) < period + 1:
        return 50
    try:
        series = pd.Series(prices)
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return int(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
    except:
        return 50
def get_support_resistance(ticker: str):
    """คำนวณหาแนวรับ-แนวต้านอัตโนมัติจากข้อมูล 3 เดือนย้อนหลัง"""
    try:
        ohlc = get_candlestick_data(ticker, period="3mo")
        if not ohlc: return 0, 0
        
        lows = sorted([d['low'] for d in ohlc])
        highs = sorted([d['high'] for d in ohlc], reverse=True)
        
        # เฉลี่ยจุดต่ำสุด 5 จุด และสูงสุด 5 จุด เพื่อความแม่นยำ
        support = sum(lows[:5]) / 5 if len(lows) >= 5 else lows[0]
        resistance = sum(highs[:5]) / 5 if len(highs) >= 5 else highs[0]
        return round(support, 2), round(resistance, 2)
    except:
        return 0, 0    