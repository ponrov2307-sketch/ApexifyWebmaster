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
SPARKLINE_CACHE_TIME = {}
SPARKLINE_CACHE_TTL = 120
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

def _extract_close_series(download_df, ticker: str):
    if download_df is None or download_df.empty:
        return pd.Series(dtype=float)
    try:
        close_data = download_df['Close']
        if isinstance(close_data, pd.DataFrame):
            if ticker in close_data.columns:
                return close_data[ticker].dropna()
            return close_data.iloc[:, 0].dropna()
        return close_data.dropna()
    except Exception:
        return pd.Series(dtype=float)


def _compute_return_metrics(values: pd.Series):
    if values is None or values.empty or len(values) < 2:
        return {'return_pct': 0.0, 'max_drawdown_pct': 0.0, 'volatility_annual_pct': 0.0}

    base = float(values.iloc[0]) if float(values.iloc[0]) != 0 else 1.0
    total_return = ((float(values.iloc[-1]) / base) - 1) * 100

    peak = values.cummax()
    drawdown = ((values - peak) / peak) * 100
    max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0

    daily = values.pct_change().dropna()
    volatility = float(daily.std() * (252 ** 0.5) * 100) if not daily.empty else 0.0

    return {
        'return_pct': round(total_return, 2),
        'max_drawdown_pct': round(max_drawdown, 2),
        'volatility_annual_pct': round(volatility, 2),
    }


def get_portfolio_historical_growth(portfolio_items: list, period: str = "1y", interval: str = "1d", benchmark: str = "SPY"):
    if not portfolio_items:
        return {
            'labels': [],
            'portfolio_values': [],
            'benchmark_values': [],
            'benchmark_ticker': benchmark,
            'portfolio_metrics': _compute_return_metrics(pd.Series(dtype=float)),
            'benchmark_metrics': _compute_return_metrics(pd.Series(dtype=float)),
            'updated_at': datetime.now(UTC).isoformat(),
        }

    tickers = [str(item.get('ticker', '')).strip().upper() for item in portfolio_items if item.get('ticker')]
    tickers = [t for t in tickers if t]
    if not tickers:
        return {
            'labels': [],
            'portfolio_values': [],
            'benchmark_values': [],
            'benchmark_ticker': benchmark,
            'portfolio_metrics': _compute_return_metrics(pd.Series(dtype=float)),
            'benchmark_metrics': _compute_return_metrics(pd.Series(dtype=float)),
            'updated_at': datetime.now(UTC).isoformat(),
        }

    try:
        data = yf.download(tickers, period=period, interval=interval, progress=False, auto_adjust=True)
        if data.empty:
            return {
                'labels': [],
                'portfolio_values': [],
                'benchmark_values': [],
                'benchmark_ticker': benchmark,
                'portfolio_metrics': _compute_return_metrics(pd.Series(dtype=float)),
                'benchmark_metrics': _compute_return_metrics(pd.Series(dtype=float)),
                'updated_at': datetime.now(UTC).isoformat(),
            }

        portfolio_df = pd.DataFrame(index=data.index)
        portfolio_df['portfolio_value'] = 0.0

        for item in portfolio_items:
            t = str(item.get('ticker', '')).strip().upper()
            if not t:
                continue
            shares = float(item.get('shares', 0) or 0)
            close_series = _extract_close_series(data, t).reindex(data.index).ffill().fillna(0.0)
            portfolio_df['portfolio_value'] += close_series * shares

        benchmark_df = yf.download(str(benchmark).upper(), period=period, interval=interval, progress=False, auto_adjust=True)
        bench_close = _extract_close_series(benchmark_df, str(benchmark).upper()).reindex(portfolio_df.index).ffill()

        merged = pd.DataFrame(index=portfolio_df.index)
        merged['portfolio_value'] = portfolio_df['portfolio_value']
        merged = merged[merged['portfolio_value'] > 0]
        if not bench_close.empty:
            merged['bench_close'] = bench_close
            merged = merged.dropna()

        if merged.empty:
            return {
                'labels': [],
                'portfolio_values': [],
                'benchmark_values': [],
                'benchmark_ticker': benchmark,
                'portfolio_metrics': _compute_return_metrics(pd.Series(dtype=float)),
                'benchmark_metrics': _compute_return_metrics(pd.Series(dtype=float)),
                'updated_at': datetime.now(UTC).isoformat(),
            }

        portfolio_values = merged['portfolio_value']
        base_portfolio = float(portfolio_values.iloc[0]) if float(portfolio_values.iloc[0]) != 0 else 1.0

        benchmark_values = []
        benchmark_metrics = _compute_return_metrics(pd.Series(dtype=float))
        if 'bench_close' in merged.columns:
            bench_norm = (merged['bench_close'] / float(merged['bench_close'].iloc[0])) * base_portfolio
            benchmark_values = [round(float(v), 2) for v in bench_norm.tolist()]
            benchmark_metrics = _compute_return_metrics(bench_norm)

        return {
            'labels': merged.index.strftime('%Y-%m-%d').tolist(),
            'portfolio_values': [round(float(v), 2) for v in portfolio_values.tolist()],
            'benchmark_values': benchmark_values,
            'benchmark_ticker': str(benchmark).upper(),
            'portfolio_metrics': _compute_return_metrics(portfolio_values),
            'benchmark_metrics': benchmark_metrics,
            'updated_at': datetime.now(UTC).isoformat(),
        }
    except Exception:
        return {
            'labels': [],
            'portfolio_values': [],
            'benchmark_values': [],
            'benchmark_ticker': benchmark,
            'portfolio_metrics': _compute_return_metrics(pd.Series(dtype=float)),
            'benchmark_metrics': _compute_return_metrics(pd.Series(dtype=float)),
            'updated_at': datetime.now(UTC).isoformat(),
        }

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


# ---------- v2 data services for DRIP / Growth / Sector Flow ----------
def get_drip_projection(
    initial_capital: float = 10000.0,
    monthly_contribution: float = 0.0,
    dividend_yield_pct: float = 3.0,
    price_growth_pct: float = 5.0,
    years: int = 10,
    tax_rate_pct: float = 0.0,
):
    initial = max(float(initial_capital or 0), 0.0)
    monthly = max(float(monthly_contribution or 0), 0.0)
    div_yield = max(float(dividend_yield_pct or 0), 0.0)
    growth = float(price_growth_pct or 0)
    years = max(int(years or 1), 1)
    tax_rate = min(max(float(tax_rate_pct or 0), 0.0), 100.0)

    value = initial
    rows = []
    labels = []
    values = []
    dividend_after_tax_total = 0.0

    for year in range(1, years + 1):
        start_capital = value
        yearly_contribution = monthly * 12
        value += yearly_contribution

        gross_dividend = value * (div_yield / 100.0)
        net_dividend = gross_dividend * (1 - tax_rate / 100.0)
        value += net_dividend
        dividend_after_tax_total += net_dividend

        growth_gain = value * (growth / 100.0)
        value += growth_gain

        labels.append(f'Year {year}')
        values.append(round(value, 2))
        rows.append({
            'year': year,
            'start_capital': round(start_capital, 2),
            'contribution': round(yearly_contribution, 2),
            'net_dividend': round(net_dividend, 2),
            'growth_gain': round(growth_gain, 2),
            'end_value': round(value, 2),
        })

    invested_capital = initial + (monthly * 12 * years)
    return {
        'labels': labels,
        'values': values,
        'rows': rows,
        'summary': {
            'initial_capital': round(initial, 2),
            'invested_capital': round(invested_capital, 2),
            'future_value': round(value, 2),
            'compound_profit': round(value - invested_capital, 2),
            'dividend_contribution': round(dividend_after_tax_total, 2),
        },
        'assumptions': f'Annual dividend {div_yield:.2f}%, price growth {growth:.2f}%, tax {tax_rate:.2f}%',
    }


def get_real_drip_backtest(ticker: str, years: int = 10, initial_capital: float = 10000.0):
    symbol = str(ticker or '').strip().upper()
    years = max(int(years or 1), 1)
    initial = max(float(initial_capital or 0), 0.0)
    if not symbol or initial <= 0:
        return None

    try:
        period = 'max' if years >= 50 else f'{years}y'
        hist = yf.Ticker(symbol).history(period=period, interval='1mo', auto_adjust=False)
        if hist.empty or len(hist) < 2:
            return None
        hist = hist.dropna(subset=['Close'])
        cutoff = pd.Timestamp(datetime.now()) - pd.DateOffset(years=years)
        hist = hist[hist.index >= cutoff]
        if hist.empty:
            return None

        close = hist['Close'].astype(float)
        div = hist['Dividends'].astype(float) if 'Dividends' in hist.columns else pd.Series(0.0, index=hist.index)

        base_price = float(close.iloc[0])
        if base_price <= 0:
            return None

        shares_price_only = initial / base_price
        shares_total = initial / base_price
        yearly = {}

        for idx in hist.index:
            d = float(div.loc[idx]) if idx in div.index else 0.0
            p = float(close.loc[idx])
            if d > 0 and p > 0:
                shares_total += (shares_total * d) / p

            y = idx.year
            yearly[y] = {
                'price': p,
                'price_only_value': shares_price_only * p,
                'drip_value': shares_total * p,
                'dividend_ps': d,
                'shares_total': shares_total,
            }

        rows = []
        labels = []
        price_series = []
        drip_series = []
        for y in sorted(yearly.keys()):
            row = yearly[y]
            labels.append(str(y))
            price_series.append(round(float(row['price_only_value']), 2))
            drip_series.append(round(float(row['drip_value']), 2))
            rows.append({
                'year': y,
                'price': round(float(row['price']), 2),
                'price_only_value': round(float(row['price_only_value']), 2),
                'drip_value': round(float(row['drip_value']), 2),
                'dividend_ps': round(float(row['dividend_ps']), 4),
                'shares': round(float(row['shares_total']), 6),
            })

        if not rows:
            return None

        final_price_only = float(rows[-1]['price_only_value'])
        final_drip = float(rows[-1]['drip_value'])
        total_return = ((final_drip / initial) - 1) * 100
        price_return = ((final_price_only / initial) - 1) * 100
        dividend_return = total_return - price_return

        return {
            'ticker': symbol,
            'labels': labels,
            'price_only_values': price_series,
            'drip_values': drip_series,
            'rows': rows,
            'summary': {
                'initial_capital': round(initial, 2),
                'final_price_only': round(final_price_only, 2),
                'final_drip': round(final_drip, 2),
                'price_return_pct': round(price_return, 2),
                'dividend_return_pct': round(dividend_return, 2),
                'total_return_pct': round(total_return, 2),
            },
            'updated_at': datetime.now(UTC).isoformat(),
        }
    except Exception:
        return None


def get_real_sector_rotation(window: str = '1mo', sector_map=None):
    sectors = sector_map or {
        'Technology': 'XLK',
        'Healthcare': 'XLV',
        'Financials': 'XLF',
        'Energy': 'XLE',
        'Consumer Discretionary': 'XLY',
        'Consumer Staples': 'XLP',
        'Industrials': 'XLI',
        'Utilities': 'XLU',
        'Real Estate': 'XLRE',
        'Materials': 'XLB',
        'Communication': 'XLC',
    }
    result = []
    for name, sym in sectors.items():
        try:
            hist = yf.Ticker(sym).history(period=window, interval='1d', auto_adjust=True)
            if hist.empty or len(hist) < 2:
                continue
            close = hist['Close'].dropna()
            if len(close) < 2:
                continue
            flow_pct = ((float(close.iloc[-1]) - float(close.iloc[0])) / float(close.iloc[0])) * 100
            result.append({
                'sector': name,
                'symbol': sym,
                'flow_pct': round(flow_pct, 2),
                'sparkline': [round(float(v), 2) for v in close.tail(20).tolist()],
                'updated_at': datetime.now(UTC).isoformat(),
            })
        except Exception:
            continue

    result.sort(key=lambda x: x['flow_pct'], reverse=True)
    for i, item in enumerate(result, start=1):
        item['rank'] = i
    return result
