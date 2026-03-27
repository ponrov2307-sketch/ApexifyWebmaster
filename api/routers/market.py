"""Market data endpoints — charts, macro, indicators."""

import asyncio
import math
import time

from fastapi import APIRouter, Query

from api.deps import CurrentUser
from core.config import MARKET_INDICES
from services.yahoo_finance import (
    calculate_bollinger_bands,
    calculate_macd_series,
    calculate_rsi_series,
    get_candlestick_data,
    get_live_price,
    get_market_summary,
    get_real_fear_and_greed,
    get_real_sector_rotation,
    get_support_resistance,
    get_top_movers,
)

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/summary")
async def market_summary(user: CurrentUser):
    raw = await asyncio.to_thread(get_market_summary)
    return {"indices": raw}


def _build_chart(ticker: str, period: str, indicators: str) -> dict:
    """Synchronous helper — safe to run in a thread."""
    candles = get_candlestick_data(ticker, period=period)
    if not candles:
        return {"candles": [], "indicators": {}}

    result: dict = {"candles": candles, "indicators": {}}
    closes = [c["close"] for c in candles]
    requested = {s.strip().lower() for s in indicators.split(",") if s.strip()}

    def _clean(v):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        return v

    def _clean_list(lst):
        return [_clean(x) for x in lst]

    if "rsi" in requested and len(closes) >= 15:
        result["indicators"]["rsi"] = _clean_list(calculate_rsi_series(closes))

    if "macd" in requested and len(closes) >= 35:
        macd_line, signal_line, histogram = calculate_macd_series(closes)
        result["indicators"]["macd"] = {
            "macd": _clean_list(macd_line),
            "signal": _clean_list(signal_line),
            "histogram": _clean_list(histogram),
        }

    if "bollinger" in requested and len(closes) >= 20:
        upper, sma, lower = calculate_bollinger_bands(closes)
        result["indicators"]["bollinger"] = [
            _clean_list(upper),
            _clean_list(sma),
            _clean_list(lower),
        ]

    return result


@router.get("/chart/{ticker}")
async def chart_data(
    ticker: str,
    user: CurrentUser,
    period: str = Query("3mo", pattern="^(1mo|3mo|6mo|1y|2y|5y|10y|20y|max)$"),
    indicators: str = Query("", description="Comma-separated: rsi,macd,bollinger"),
):
    return await asyncio.to_thread(_build_chart, ticker, period, indicators)


@router.get("/price/{ticker}")
async def live_price(ticker: str, user: CurrentUser):
    price = await asyncio.to_thread(get_live_price, ticker)
    return {"ticker": ticker.upper(), "price": price or 0.0}


_MACRO_CACHE: dict = {}
_MACRO_CACHE_TIME: float = 0
_MACRO_CACHE_TTL = 300  # 5 minutes


def _fetch_macro():
    from services.yahoo_finance import batch_get_prices

    try:
        fg_value, fg_text = get_real_fear_and_greed()
    except Exception:
        fg_value, fg_text = 0, "Unavailable"

    # Batch fetch all index prices + VIX in one call
    all_tickers = list(MARKET_INDICES.keys()) + ["^VIX"]
    prices = batch_get_prices(all_tickers)
    vix = prices.get("^VIX", 0.0)

    indices = {}
    for symbol, name in MARKET_INDICES.items():
        indices[symbol] = {"name": name, "price": prices.get(symbol, 0.0)}

    try:
        raw_sectors = get_real_sector_rotation()
        sectors = {s["sector"]: s["flow_pct"] for s in raw_sectors if "sector" in s}
    except Exception:
        sectors = {}

    try:
        top_movers = get_top_movers(n=3)
    except Exception:
        top_movers = []

    return {
        "fear_greed": {"value": fg_value, "text": fg_text},
        "vix": vix,
        "indices": indices,
        "sectors": sectors,
        "top_movers": top_movers,
    }


@router.get("/macro")
async def macro_data(user: CurrentUser):
    import asyncio
    global _MACRO_CACHE, _MACRO_CACHE_TIME

    now = time.time()
    if _MACRO_CACHE and (now - _MACRO_CACHE_TIME) < _MACRO_CACHE_TTL:
        return _MACRO_CACHE

    try:
        data = await asyncio.to_thread(_fetch_macro)
        _MACRO_CACHE = data
        _MACRO_CACHE_TIME = now
        return data
    except Exception:
        return _MACRO_CACHE or {"fear_greed": {"value": 0, "text": "Unavailable"}, "vix": 0, "indices": {}, "sectors": {}}


@router.get("/support-resistance/{ticker}")
async def support_resistance(ticker: str, user: CurrentUser):
    data = await asyncio.to_thread(get_support_resistance, ticker)
    return data or {"support": [], "resistance": []}


# ── S&P 500 Heatmap ──
_SP500_BY_SECTOR: dict[str, list[str]] = {
    "Technology":        ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "AMD", "CSCO", "ADBE", "CRM", "INTU", "QCOM", "TXN", "NOW", "ACN", "MU", "AMAT", "LRCX", "KLAC", "MRVL", "PANW"],
    "Communication":     ["GOOGL", "META", "NFLX", "CMCSA", "DIS", "T", "VZ", "TMUS", "CHTR", "EA", "TTWO"],
    "Financials":        ["BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPGI", "BLK", "AXP", "CB", "PGR", "C", "USB", "TFC", "ICE", "CME"],
    "Consumer Disc.":    ["AMZN", "TSLA", "HD", "MCD", "NKE", "BKNG", "LOW", "TJX", "SBUX", "CMG", "ORLY", "AZO", "GM", "F"],
    "Healthcare":        ["LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "AMGN", "PFE", "MDT", "GILD", "ELV", "CVS", "ISRG", "BSX", "SYK"],
    "Industrials":       ["GE", "CAT", "RTX", "HON", "UNP", "LMT", "DE", "BA", "ETN", "ITW", "UPS", "EMR", "GEV", "FDX", "NSC"],
    "Consumer Staples":  ["WMT", "COST", "PG", "KO", "PEP", "PM", "MDLZ", "MO", "CL", "KHC", "STZ", "KR"],
    "Energy":            ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "OXY", "VLO", "HES", "KMI"],
    "Real Estate":       ["PLD", "AMT", "EQIX", "SPG", "DLR", "O", "PSA", "WELL", "AVB", "EQR", "CSGP"],
    "Utilities":         ["NEE", "SO", "DUK", "AEP", "SRE", "EXC", "XEL", "WEC", "ES", "AWK"],
    "Materials":         ["LIN", "SHW", "APD", "ECL", "NEM", "FCX", "NUE", "VMC", "MLM", "PPG", "ALB"],
}

# Approximate market cap weights (in $B) for realistic treemap sizing
_SP500_MCAP: dict[str, int] = {
    # Technology
    "AAPL": 3400, "MSFT": 3100, "NVDA": 2800, "AVGO": 800, "ORCL": 400, "AMD": 220, "CSCO": 230,
    "ADBE": 210, "CRM": 260, "INTU": 180, "QCOM": 190, "TXN": 180, "NOW": 200, "ACN": 210,
    "MU": 110, "AMAT": 150, "LRCX": 100, "KLAC": 95, "MRVL": 70, "PANW": 120,
    # Communication
    "GOOGL": 2100, "META": 1500, "NFLX": 350, "CMCSA": 150, "DIS": 180, "T": 150, "VZ": 170,
    "TMUS": 250, "CHTR": 50, "EA": 40, "TTWO": 30,
    # Financials
    "BRK-B": 900, "JPM": 600, "V": 550, "MA": 420, "BAC": 300, "WFC": 200, "GS": 160,
    "MS": 150, "SPGI": 150, "BLK": 140, "AXP": 170, "CB": 110, "PGR": 130, "C": 120,
    "USB": 65, "TFC": 55, "ICE": 80, "CME": 80,
    # Consumer Discretionary
    "AMZN": 2000, "TSLA": 800, "HD": 380, "MCD": 210, "NKE": 110, "BKNG": 160, "LOW": 140,
    "TJX": 120, "SBUX": 100, "CMG": 80, "ORLY": 65, "AZO": 55, "GM": 50, "F": 40,
    # Healthcare
    "LLY": 750, "UNH": 500, "JNJ": 380, "ABBV": 310, "MRK": 270, "TMO": 200, "ABT": 200,
    "DHR": 170, "BMY": 110, "AMGN": 150, "PFE": 140, "MDT": 110, "GILD": 110, "ELV": 100,
    "CVS": 80, "ISRG": 170, "BSX": 120, "SYK": 130,
    # Industrials
    "GE": 200, "CAT": 180, "RTX": 160, "HON": 140, "UNP": 150, "LMT": 120, "DE": 110,
    "BA": 130, "ETN": 130, "ITW": 80, "UPS": 100, "EMR": 70, "GEV": 80, "FDX": 60, "NSC": 55,
    # Consumer Staples
    "WMT": 600, "COST": 380, "PG": 380, "KO": 270, "PEP": 220, "PM": 200, "MDLZ": 90,
    "MO": 90, "CL": 75, "KHC": 40, "STZ": 45, "KR": 40,
    # Energy
    "XOM": 470, "CVX": 270, "COP": 130, "SLB": 60, "EOG": 70, "MPC": 55, "PSX": 50,
    "OXY": 40, "VLO": 45, "HES": 45, "KMI": 45,
    # Real Estate
    "PLD": 100, "AMT": 90, "EQIX": 80, "SPG": 55, "DLR": 45, "O": 50, "PSA": 50,
    "WELL": 45, "AVB": 30, "EQR": 25, "CSGP": 35,
    # Utilities
    "NEE": 160, "SO": 95, "DUK": 85, "AEP": 50, "SRE": 50, "EXC": 40, "XEL": 35,
    "WEC": 30, "ES": 25, "AWK": 28,
    # Materials
    "LIN": 210, "SHW": 85, "APD": 65, "ECL": 55, "NEM": 50, "FCX": 60, "NUE": 35,
    "VMC": 35, "MLM": 35, "PPG": 30, "ALB": 10,
}

_SP500_CACHE: dict = {}
_SP500_CACHE_TIME: float = 0
_SP500_CACHE_TTL = 300  # 5 minutes


def _fetch_sp500_data() -> dict:
    import yfinance as yf
    all_tickers = [t for tickers in _SP500_BY_SECTOR.values() for t in tickers]
    try:
        raw = yf.download(all_tickers, period="2d", interval="1d", progress=False, auto_adjust=True)
        closes = raw["Close"] if "Close" in raw else raw
        result: dict[str, list[dict]] = {}
        for sector, tickers in _SP500_BY_SECTOR.items():
            stocks = []
            for t in tickers:
                try:
                    col = t if t in closes.columns else None
                    if col is None:
                        continue
                    vals = closes[col].dropna().values
                    if len(vals) < 2:
                        continue
                    price = float(vals[-1])
                    prev  = float(vals[-2])
                    chg   = round((price - prev) / prev * 100, 2) if prev else 0.0
                    stocks.append({"ticker": t, "price": round(price, 2), "change_pct": chg, "mcap": _SP500_MCAP.get(t, 30)})
                except Exception:
                    continue
            result[sector] = stocks
        return result
    except Exception:
        return {}


@router.get("/sp500-heatmap")
async def sp500_heatmap(user: CurrentUser):
    """Return S&P 500 stocks grouped by sector with today's price change. Cached 5 min."""
    global _SP500_CACHE, _SP500_CACHE_TIME
    import asyncio

    now = time.time()
    if _SP500_CACHE and (now - _SP500_CACHE_TIME) < _SP500_CACHE_TTL:
        return _SP500_CACHE

    data = await asyncio.to_thread(_fetch_sp500_data)
    if data:
        _SP500_CACHE = data
        _SP500_CACHE_TIME = now
    return data or _SP500_CACHE


# ── Economic Calendar ──
_ECON_EVENTS = [
    # 2026 Q1
    {"date": "2026-01-10", "event": "Non-Farm Payrolls", "category": "employment", "impact": "high"},
    {"date": "2026-01-14", "event": "CPI (Consumer Price Index)", "category": "inflation", "impact": "high"},
    {"date": "2026-01-29", "event": "FOMC Rate Decision", "category": "fed", "impact": "high"},
    {"date": "2026-01-30", "event": "GDP Q4 Advance", "category": "gdp", "impact": "high"},
    {"date": "2026-02-07", "event": "Non-Farm Payrolls", "category": "employment", "impact": "high"},
    {"date": "2026-02-12", "event": "CPI", "category": "inflation", "impact": "high"},
    {"date": "2026-02-20", "event": "FOMC Minutes", "category": "fed", "impact": "medium"},
    {"date": "2026-02-27", "event": "GDP Q4 Second Estimate", "category": "gdp", "impact": "medium"},
    {"date": "2026-03-06", "event": "Non-Farm Payrolls", "category": "employment", "impact": "high"},
    {"date": "2026-03-11", "event": "CPI", "category": "inflation", "impact": "high"},
    {"date": "2026-03-18", "event": "FOMC Rate Decision", "category": "fed", "impact": "high"},
    {"date": "2026-03-26", "event": "GDP Q4 Final", "category": "gdp", "impact": "medium"},
    # 2026 Q2
    {"date": "2026-04-03", "event": "Non-Farm Payrolls", "category": "employment", "impact": "high"},
    {"date": "2026-04-10", "event": "CPI", "category": "inflation", "impact": "high"},
    {"date": "2026-04-09", "event": "FOMC Minutes", "category": "fed", "impact": "medium"},
    {"date": "2026-04-29", "event": "GDP Q1 Advance", "category": "gdp", "impact": "high"},
    {"date": "2026-05-01", "event": "Non-Farm Payrolls", "category": "employment", "impact": "high"},
    {"date": "2026-05-06", "event": "FOMC Rate Decision", "category": "fed", "impact": "high"},
    {"date": "2026-05-12", "event": "CPI", "category": "inflation", "impact": "high"},
    {"date": "2026-05-28", "event": "GDP Q1 Second Estimate", "category": "gdp", "impact": "medium"},
    {"date": "2026-06-05", "event": "Non-Farm Payrolls", "category": "employment", "impact": "high"},
    {"date": "2026-06-10", "event": "CPI", "category": "inflation", "impact": "high"},
    {"date": "2026-06-17", "event": "FOMC Rate Decision", "category": "fed", "impact": "high"},
    {"date": "2026-06-25", "event": "GDP Q1 Final", "category": "gdp", "impact": "medium"},
    # 2026 Q3
    {"date": "2026-07-02", "event": "Non-Farm Payrolls", "category": "employment", "impact": "high"},
    {"date": "2026-07-14", "event": "CPI", "category": "inflation", "impact": "high"},
    {"date": "2026-07-29", "event": "FOMC Rate Decision", "category": "fed", "impact": "high"},
    {"date": "2026-07-30", "event": "GDP Q2 Advance", "category": "gdp", "impact": "high"},
    {"date": "2026-08-07", "event": "Non-Farm Payrolls", "category": "employment", "impact": "high"},
    {"date": "2026-08-12", "event": "CPI", "category": "inflation", "impact": "high"},
    {"date": "2026-08-19", "event": "FOMC Minutes", "category": "fed", "impact": "medium"},
    {"date": "2026-09-04", "event": "Non-Farm Payrolls", "category": "employment", "impact": "high"},
    {"date": "2026-09-10", "event": "CPI", "category": "inflation", "impact": "high"},
    {"date": "2026-09-16", "event": "FOMC Rate Decision", "category": "fed", "impact": "high"},
    {"date": "2026-09-25", "event": "GDP Q2 Final", "category": "gdp", "impact": "medium"},
    # 2026 Q4
    {"date": "2026-10-02", "event": "Non-Farm Payrolls", "category": "employment", "impact": "high"},
    {"date": "2026-10-13", "event": "CPI", "category": "inflation", "impact": "high"},
    {"date": "2026-10-07", "event": "FOMC Minutes", "category": "fed", "impact": "medium"},
    {"date": "2026-10-29", "event": "GDP Q3 Advance", "category": "gdp", "impact": "high"},
    {"date": "2026-11-06", "event": "Non-Farm Payrolls", "category": "employment", "impact": "high"},
    {"date": "2026-11-04", "event": "FOMC Rate Decision", "category": "fed", "impact": "high"},
    {"date": "2026-11-12", "event": "CPI", "category": "inflation", "impact": "high"},
    {"date": "2026-11-25", "event": "GDP Q3 Second Estimate", "category": "gdp", "impact": "medium"},
    {"date": "2026-12-04", "event": "Non-Farm Payrolls", "category": "employment", "impact": "high"},
    {"date": "2026-12-10", "event": "CPI", "category": "inflation", "impact": "high"},
    {"date": "2026-12-16", "event": "FOMC Rate Decision", "category": "fed", "impact": "high"},
    {"date": "2026-12-23", "event": "GDP Q3 Final", "category": "gdp", "impact": "medium"},
]


@router.get("/economic-calendar")
async def economic_calendar(user: CurrentUser):
    """Return upcoming economic events."""
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc).date()
    past_limit = now - timedelta(days=7)

    events = [
        e for e in sorted(_ECON_EVENTS, key=lambda x: x["date"])
        if e["date"] >= past_limit.isoformat()
    ]
    return {"events": events}


import pathlib as _pathlib

_LOGO_DIR = _pathlib.Path(__file__).resolve().parent.parent.parent / "static" / "logos"
_LOGO_DIR.mkdir(parents=True, exist_ok=True)


_SLUG_CACHE: dict = {}

def _ticker_to_slug(ticker: str) -> list[str]:
    """Convert ticker to possible TradingView company-name slugs via yfinance."""
    if ticker in _SLUG_CACHE:
        return _SLUG_CACHE[ticker]
    import re
    try:
        from services.yahoo_finance import get_ticker_info
        info = get_ticker_info(ticker)
        name = info.get("name", "")
        if name:
            name = name.lower()
            # Remove suffixes — longest first to avoid partial matches
            for suffix in [" corporation", ", inc.", " inc.", " incorporated",
                           " corp.", " corp", " company", " companies",
                           " co., ltd.", " co., ltd", " co.", " co",
                           " ltd.", " ltd", " plc", " sa", " se", " ag", " nv",
                           ", inc", " inc",
                           " holdings", " group", " international", " & co",
                           " class a", " class b", " class c"]:
                if name.endswith(suffix):
                    name = name[:-len(suffix)]
                    break
            name = name.strip().rstrip(",").strip()
            # Remove leading "the "
            if name.startswith("the "):
                name = name[4:]
            slug = re.sub(r"[^a-z0-9]+", "-", name).strip("-")
            # Remove trailing "-the" or "-company-the"
            slug = re.sub(r"-company-the$", "", slug)
            slug = re.sub(r"-the$", "", slug)
            first_word = slug.split("-")[0]
            slugs = [slug]
            if first_word != slug:
                slugs.append(first_word)
            _SLUG_CACHE[ticker] = slugs
            return slugs
    except Exception:
        pass
    _SLUG_CACHE[ticker] = []
    return []


def _make_fallback_svg(ticker: str) -> str:
    """Generate a styled fallback SVG with ticker initials."""
    initials = ticker.replace(".BK", "")[:2].upper()
    # Color based on ticker
    hue = sum(ord(c) for c in ticker) % 360
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
      <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="hsl({hue},60%,25%)"/>
        <stop offset="100%" stop-color="hsl({hue},40%,15%)"/>
      </linearGradient></defs>
      <rect width="128" height="128" rx="64" fill="url(#g)"/>
      <text x="64" y="74" font-family="Arial,sans-serif" font-size="42" font-weight="bold" fill="hsl({hue},70%,75%)" text-anchor="middle">{initials}</text>
    </svg>'''


@router.get("/logo/{ticker}")
async def stock_logo(ticker: str):
    """Proxy stock logo from TradingView — cached to disk."""
    import asyncio
    import httpx
    from fastapi.responses import Response, FileResponse

    clean = ticker.strip().upper().replace(".BK", "")

    # Check disk cache first (includes previously saved fallbacks)
    for ext in (".svg", ".png"):
        cached_path = _LOGO_DIR / f"{clean}{ext}"
        if cached_path.exists() and cached_path.stat().st_size > 100:
            media = "image/svg+xml" if ext == ".svg" else "image/png"
            return FileResponse(str(cached_path), media_type=media, headers={"Cache-Control": "public, max-age=86400"})

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://www.tradingview.com/",
    }

    slugs = await asyncio.to_thread(_ticker_to_slug, clean)
    urls = []
    for slug in slugs:
        urls.append(f"https://s3-symbol-logo.tradingview.com/{slug}--big.svg")
    urls.append(f"https://s3-symbol-logo.tradingview.com/{clean.lower()}--big.svg")

    async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
        for url in urls:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200 and len(resp.content) > 100:
                    content_type = resp.headers.get("content-type", "image/png")
                    ext = ".svg" if "svg" in content_type else ".png"
                    save_path = _LOGO_DIR / f"{clean}{ext}"
                    save_path.write_bytes(resp.content)
                    return Response(
                        content=resp.content,
                        media_type=content_type,
                        headers={"Cache-Control": "public, max-age=86400"},
                    )
            except Exception:
                continue

    # Fallback: save styled SVG to disk so we don't retry TradingView next time
    svg = _make_fallback_svg(clean)
    save_path = _LOGO_DIR / f"{clean}.svg"
    save_path.write_text(svg, encoding="utf-8")
    return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})


# ── Earnings Calendar ──
_EARNINGS_CACHE: dict = {}
_EARNINGS_CACHE_TIME: float = 0
_EARNINGS_CACHE_TTL = 3600  # 1 hour


def _fetch_earnings(tickers: list[str]) -> list[dict]:
    """Fetch next earnings dates for a list of tickers using yfinance."""
    import yfinance as yf
    from datetime import datetime, timezone

    results = []
    now = datetime.now(timezone.utc)

    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            cal = t.calendar
            if cal is None or (hasattr(cal, "empty") and cal.empty):
                continue

            # yfinance calendar can be a dict or DataFrame
            if isinstance(cal, dict):
                date_val = cal.get("Earnings Date")
                if isinstance(date_val, list) and date_val:
                    date_val = date_val[0]
                eps_est = cal.get("Earnings Average") or cal.get("EPS Estimate")
                rev_est = cal.get("Revenue Average") or cal.get("Revenue Estimate")
            else:
                # DataFrame format
                if "Earnings Date" in cal.columns:
                    date_val = cal["Earnings Date"].iloc[0] if len(cal) > 0 else None
                elif len(cal.columns) > 0:
                    date_val = cal.iloc[0, 0] if len(cal) > 0 else None
                else:
                    date_val = None
                eps_est = None
                rev_est = None

            if date_val is None:
                continue

            # Parse date
            if hasattr(date_val, "isoformat"):
                date_str = date_val.strftime("%Y-%m-%d")
            else:
                date_str = str(date_val)[:10]

            results.append({
                "ticker": ticker.upper(),
                "date": date_str,
                "eps_estimate": round(float(eps_est), 2) if eps_est else None,
                "revenue_estimate": round(float(rev_est), 0) if rev_est else None,
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["date"])
    return results


@router.get("/earnings-calendar")
async def earnings_calendar(user: CurrentUser):
    """Return upcoming earnings dates for user's portfolio stocks. Cached 1 hour."""
    import asyncio
    global _EARNINGS_CACHE, _EARNINGS_CACHE_TIME

    now = time.time()
    uid = user.user_id

    # Per-user cache key
    cache_key = f"earnings_{uid}"
    if cache_key in _EARNINGS_CACHE and (now - _EARNINGS_CACHE_TIME) < _EARNINGS_CACHE_TTL:
        return _EARNINGS_CACHE[cache_key]

    # Get user's portfolio tickers
    from core.models import get_portfolio
    portfolio = get_portfolio(uid)
    tickers = [p["ticker"] for p in portfolio]

    if not tickers:
        return {"earnings": []}

    data = await asyncio.to_thread(_fetch_earnings, tickers)
    result = {"earnings": data}
    _EARNINGS_CACHE[cache_key] = result
    _EARNINGS_CACHE_TIME = now
    return result


# ── Portfolio vs Benchmark ──
_BENCH_CACHE: dict = {}
_BENCH_CACHE_TTL = 600  # 10 minutes


@router.get("/benchmark")
async def portfolio_benchmark(
    user: CurrentUser,
    period: str = Query("1y", pattern="^(1mo|3mo|6mo|1y|2y|3y|5y)$"),
    benchmark: str = Query("SPY"),
):
    """Return portfolio growth vs benchmark (SPY/QQQ). Cached 10 min."""
    import asyncio
    from services.yahoo_finance import get_portfolio_historical_growth
    from core.models import get_portfolio

    now = time.time()
    uid = user.user_id
    cache_key = f"bench_{uid}_{period}_{benchmark}"

    if cache_key in _BENCH_CACHE and (now - _BENCH_CACHE.get(f"{cache_key}_t", 0)) < _BENCH_CACHE_TTL:
        return _BENCH_CACHE[cache_key]

    portfolio = get_portfolio(uid)
    if not portfolio:
        return {"labels": [], "portfolio_values": [], "benchmark_values": [], "benchmark_ticker": benchmark, "portfolio_metrics": {}, "benchmark_metrics": {}}

    portfolio_items = [{"ticker": p["ticker"], "shares": p["shares"]} for p in portfolio]

    # Map period labels
    period_map = {"1mo": "1mo", "3mo": "3mo", "6mo": "6mo", "1y": "1y", "2y": "2y", "3y": "3y", "5y": "5y"}
    yf_period = period_map.get(period, "1y")

    data = await asyncio.to_thread(
        get_portfolio_historical_growth,
        portfolio_items, period=yf_period, interval="1d", benchmark=benchmark.upper()
    )

    _BENCH_CACHE[cache_key] = data
    _BENCH_CACHE[f"{cache_key}_t"] = now
    return data
