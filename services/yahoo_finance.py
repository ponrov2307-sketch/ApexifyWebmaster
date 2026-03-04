import yfinance as yf
import pandas as pd
from datetime import datetime, UTC
from core.config import MARKET_INDICES
import requests # 🌟 เพิ่มไว้บรรทัดบนสุดของไฟล์
import time
# 🌟 พื้นที่จดจำราคาหุ้นส่วนกลาง (Global Cache)
GLOBAL_PRICE_CACHE = {}
GLOBAL_SPARKLINE_CACHE = {}
PRICE_CACHE_TIME = {}
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
    now = time.time()
    
    # 🌟 ถ้าราคาเพิ่งดึงมา "ไม่ถึง 10 วินาที" ค่อยใช้ของเดิม
    if ticker in GLOBAL_PRICE_CACHE and (now - PRICE_CACHE_TIME.get(ticker, 0)) < 10:
        return GLOBAL_PRICE_CACHE[ticker]
        
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if data.empty: return GLOBAL_PRICE_CACHE.get(ticker, 0.0)
        
        if isinstance(data.columns, pd.MultiIndex):
            price = float(data['Close'][ticker].dropna().iloc[-1])
        else:
            price = float(data['Close'].dropna().iloc[-1])
            
        # 🌟 อัปเดตราคาใหม่ และประทับเวลา
        GLOBAL_PRICE_CACHE[ticker] = price
        PRICE_CACHE_TIME[ticker] = now
        
        return price
    except: 
        return GLOBAL_PRICE_CACHE.get(ticker, 0.0)

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


def _calc_max_drawdown(series: pd.Series) -> float:
    if series is None or series.empty:
        return 0.0
    peak = series.cummax()
    drawdown = ((series - peak) / peak) * 100
    return float(round(drawdown.min(), 2))


def get_stock_duel_data(ticker_a: str, ticker_b: str, years: int = 10, initial_capital: float = 10000.0):
    """Compare two stocks over a selected horizon and return chart+table ready data."""
    try:
        ticker_a = str(ticker_a or '').strip().upper()
        ticker_b = str(ticker_b or '').strip().upper()
        years = int(years or 10)
        if not ticker_a or not ticker_b:
            return None

        period = 'max' if years >= 50 else f'{years}y'
        interval = '1mo'

        data_a = yf.download(ticker_a, period=period, interval=interval, progress=False, auto_adjust=True)
        data_b = yf.download(ticker_b, period=period, interval=interval, progress=False, auto_adjust=True)
        if data_a.empty or data_b.empty:
            return None

        close_a = data_a['Close']
        close_b = data_b['Close']
        if isinstance(close_a, pd.DataFrame):
            close_a = close_a.iloc[:, 0]
        if isinstance(close_b, pd.DataFrame):
            close_b = close_b.iloc[:, 0]

        close_a = close_a.dropna()
        close_b = close_b.dropna()
        if close_a.empty or close_b.empty:
            return None

        df = pd.concat([close_a.rename('a_close'), close_b.rename('b_close')], axis=1).dropna()
        if df.empty:
            return None

        # Ensure requested horizon even when provider returns extra history.
        if years > 0:
            cutoff = pd.Timestamp(datetime.now()) - pd.DateOffset(years=years)
            df = df[df.index >= cutoff]
            if df.empty:
                return None

        a_base = float(df['a_close'].iloc[0])
        b_base = float(df['b_close'].iloc[0])
        if a_base <= 0 or b_base <= 0:
            return None

        a_shares = float(initial_capital) / a_base
        b_shares = float(initial_capital) / b_base

        df['a_value'] = df['a_close'] * a_shares
        df['b_value'] = df['b_close'] * b_shares
        df['a_return_pct'] = ((df['a_close'] / a_base) - 1) * 100
        df['b_return_pct'] = ((df['b_close'] / b_base) - 1) * 100

        days_span = max((df.index[-1] - df.index[0]).days, 1)
        years_span = max(days_span / 365.25, 0.01)

        a_total = float(df['a_return_pct'].iloc[-1])
        b_total = float(df['b_return_pct'].iloc[-1])
        a_cagr = ((df['a_value'].iloc[-1] / float(initial_capital)) ** (1 / years_span) - 1) * 100
        b_cagr = ((df['b_value'].iloc[-1] / float(initial_capital)) ** (1 / years_span) - 1) * 100

        result = {
            'ticker_a': ticker_a,
            'ticker_b': ticker_b,
            'years': years,
            'initial_capital': float(initial_capital),
            'labels': df.index.strftime('%Y-%m').tolist(),
            'a_close': [round(float(v), 2) for v in df['a_close'].tolist()],
            'b_close': [round(float(v), 2) for v in df['b_close'].tolist()],
            'a_value': [round(float(v), 2) for v in df['a_value'].tolist()],
            'b_value': [round(float(v), 2) for v in df['b_value'].tolist()],
            'a_return_pct': [round(float(v), 2) for v in df['a_return_pct'].tolist()],
            'b_return_pct': [round(float(v), 2) for v in df['b_return_pct'].tolist()],
            'summary': {
                'a_total_return': round(a_total, 2),
                'b_total_return': round(b_total, 2),
                'a_cagr': round(float(a_cagr), 2),
                'b_cagr': round(float(b_cagr), 2),
                'a_final_value': round(float(df['a_value'].iloc[-1]), 2),
                'b_final_value': round(float(df['b_value'].iloc[-1]), 2),
                'a_max_drawdown': _calc_max_drawdown(df['a_value']),
                'b_max_drawdown': _calc_max_drawdown(df['b_value']),
            }
        }
        return result
    except Exception:
        return None

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
# เพิ่มใน services/yahoo_finance.py
def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """คำนวณเส้นกรอบ Bollinger Bands"""
    import numpy as np
    
    if len(prices) < period:
        return [], [], []
    
    series = pd.Series(prices)
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    return round(upper, 2).tolist(), round(sma, 2).tolist(), round(lower, 2).tolist()
# ==========================================
# 🌟 REAL DATA FUNCTIONS (ล้าง Mockup)
# ==========================================

def get_real_rsi(ticker, period=14):
    """ดึงข้อมูลราคามาคำนวณ RSI จริงๆ"""
    try:
        hist = yf.Ticker(ticker).history(period="1mo")
        if len(hist) < period: return 50.0
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi.iloc[-1], 2)
    except:
        return 50.0

def get_real_fear_and_greed():
    """ดึงค่า F&G ของจริงจาก CNN"""
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        score = int(data['fear_and_greed']['score'])
        rating = data['fear_and_greed']['rating']
        return score, rating.upper()
    except:
        return 50, "NEUTRAL"

def get_analyst_target(ticker):
    """ดึงเป้าหมายราคานักวิเคราะห์ของจริง"""
    try:
        info = yf.Ticker(ticker).info
        current = info.get('currentPrice', info.get('regularMarketPrice', 0))
        target = info.get('targetMeanPrice', 0)
        if target > 0 and current > 0:
            upside = ((target - current) / current) * 100
            return target, round(upside, 2)
        return 0.0, 0.0
    except:
        return 0.0, 0.0

def get_real_sector_rotation():
    """เช็คกระแสเงินไหลเข้า Sector ผ่าน ETF ของจริง"""
    sectors = {'Tech': 'XLK', 'Health': 'XLV', 'Finance': 'XLF', 'Energy': 'XLE', 'Consumer': 'XLY'}
    rotation = []
    for name, sym in sectors.items():
        try:
            hist = yf.Ticker(sym).history(period="5d")
            if len(hist) >= 2:
                flow = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                rotation.append({'sector': name, 'flow_pct': round(flow, 2)})
        except: continue
    rotation.sort(key=lambda x: x['flow_pct'], reverse=True)
    return rotation
