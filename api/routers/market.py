"""Market data endpoints — charts, macro, indicators."""

import math

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
)

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/summary")
async def market_summary(user: CurrentUser):
    raw = get_market_summary()
    return {"indices": raw}


@router.get("/chart/{ticker}")
async def chart_data(
    ticker: str,
    user: CurrentUser,
    period: str = Query("3mo", pattern="^(1mo|3mo|6mo|1y|2y|5y|10y|20y|max)$"),
    indicators: str = Query("", description="Comma-separated: rsi,macd,bollinger"),
):
    candles = get_candlestick_data(ticker, period=period)
    if not candles:
        return {"candles": [], "indicators": {}}

    result: dict = {"candles": candles, "indicators": {}}

    closes = [c["close"] for c in candles]
    requested = {s.strip().lower() for s in indicators.split(",") if s.strip()}

    def _clean(v):
        """Replace NaN/Inf with None so JSON serialization works."""
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


@router.get("/price/{ticker}")
async def live_price(ticker: str, user: CurrentUser):
    price = get_live_price(ticker)
    return {"ticker": ticker.upper(), "price": price or 0.0}


@router.get("/macro")
async def macro_data(user: CurrentUser):
    try:
        fg_value, fg_text = get_real_fear_and_greed()
    except Exception:
        fg_value, fg_text = 0, "Unavailable"

    vix = get_live_price("^VIX") or 0.0

    indices = {}
    for symbol, name in MARKET_INDICES.items():
        price = get_live_price(symbol)
        indices[symbol] = {"name": name, "price": price or 0.0}

    try:
        raw_sectors = get_real_sector_rotation()
        sectors = {s["sector"]: s["flow_pct"] for s in raw_sectors if "sector" in s}
    except Exception:
        sectors = {}

    return {
        "fear_greed": {"value": fg_value, "text": fg_text},
        "vix": vix,
        "indices": indices,
        "sectors": sectors,
    }


@router.get("/support-resistance/{ticker}")
async def support_resistance(ticker: str, user: CurrentUser):
    data = get_support_resistance(ticker)
    return data or {"support": [], "resistance": []}


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
