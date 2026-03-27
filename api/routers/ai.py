"""AI-powered endpoints (Port Doctor, Rebalance, Copilot)."""

import asyncio
import random
import time

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.deps import CurrentUser
from services.gemini_ai import (
    generate_copilot_reply,
    generate_matchmaker_pool,
    generate_morning_briefing,
    generate_port_doctor_diagnosis,
    generate_rebalance_strategy,
)
from services.yahoo_finance import get_advanced_stock_info, get_live_price, get_real_fear_and_greed, get_real_sector_rotation, get_sparkline_data, get_ticker_info, GLOBAL_PRICE_CACHE, GLOBAL_SPARKLINE_CACHE

router = APIRouter(prefix="/api/ai", tags=["ai"])

# ── Shared matchmaker pool (server-wide, all users share this) ──
_POOL: list[dict] = []          # enriched recommendations pool
_POOL_TIME: float = 0
_POOL_TTL = 86400 * 3           # 3 days
_POOL_GENERATING = False        # prevent concurrent generation
# Per-user tracking: which tickers each user has already seen
_USER_SEEN: dict[str, set[str]] = {}  # user_id -> set of tickers


class PortDoctorRequest(BaseModel):
    portfolio: str


class RebalanceRequest(BaseModel):
    portfolio: str


class CopilotRequest(BaseModel):
    message: str


class MatchmakerRequest(BaseModel):
    tickers: list[str]
    watchlist: list[str] = []
    refresh: bool = False


def _enrich_recommendation(rec: dict, fast: bool = False) -> dict:
    """Enrich a single recommendation with price/info.

    fast=True: only use preloaded caches, no API calls (for bulk pool enrichment).
    fast=False: fall back to yfinance API if not in cache.
    """
    ticker = rec.get("ticker", "")

    # Price from preloaded cache
    price = GLOBAL_PRICE_CACHE.get(ticker, 0.0)
    if price <= 0 and not fast:
        price = get_live_price(ticker) or 0.0

    # Sparkline from preloaded cache
    sparkline = GLOBAL_SPARKLINE_CACHE.get(ticker, [])
    if not sparkline and not fast:
        spark_result = get_sparkline_data(ticker, days=30)
        sparkline = spark_result[0] if spark_result else []

    # Ticker info (has its own internal cache)
    info: dict = {}
    if not fast:
        try:
            info = get_ticker_info(ticker)
        except Exception:
            pass

    return {
        **rec,
        "price": round(price, 2),
        "market_cap": info.get("market_cap", 0),
        "pe_ratio": info.get("pe_ratio", 0),
        "div_yield": info.get("div_yield", 0),
        "52w_high": info.get("52w_high", 0),
        "52w_low": info.get("52w_low", 0),
        "beta": info.get("beta", 0),
        "target_price": info.get("target_price", 0),
        "recommendation": info.get("recommendation", ""),
        "sparkline": sparkline,
    }


def _ensure_pool(force: bool = False) -> None:
    """Generate or refresh the shared recommendation pool."""
    global _POOL, _POOL_TIME, _POOL_GENERATING

    now = time.time()
    if not force and _POOL and (now - _POOL_TIME) < _POOL_TTL:
        return  # pool still valid

    if _POOL_GENERATING:
        return  # another request is already generating

    _POOL_GENERATING = True
    try:
        # Exclude tickers already in pool to get fresh ones
        existing_tickers = {r.get("ticker", "").upper() for r in _POOL}
        recs = generate_matchmaker_pool(exclude_tickers=existing_tickers)
        if not recs:
            return

        # Fast enrich (cache only, no API calls) — instant for 100 items
        enriched = []
        for rec in recs:
            try:
                enriched.append(_enrich_recommendation(rec, fast=True))
            except Exception:
                enriched.append({**rec, "price": 0, "sparkline": []})

        if force:
            existing_tickers_in_pool = {r.get("ticker", "").upper() for r in _POOL}
            for e in enriched:
                if e.get("ticker", "").upper() not in existing_tickers_in_pool:
                    _POOL.append(e)
        else:
            _POOL = enriched

        _POOL_TIME = now
    finally:
        _POOL_GENERATING = False


def _run_matchmaker(uid: str, portfolio_tickers: list[str], watchlist_tickers: list[str]) -> list[dict]:
    """Synchronous matchmaker logic — runs in a thread pool."""
    global _POOL, _POOL_GENERATING

    # Build exclusion set: portfolio + watchlist + already seen by this user
    exclude = {t.upper() for t in portfolio_tickers}
    exclude |= {t.upper() for t in watchlist_tickers}
    exclude |= _USER_SEEN.get(uid, set())

    _ensure_pool(force=False)

    # If pool is still being generated (startup or expired), wait up to 90s
    if not _POOL and _POOL_GENERATING:
        waited = 0
        while _POOL_GENERATING and waited < 90:
            time.sleep(1)
            waited += 1
        # If still empty after waiting, try one more time
        if not _POOL:
            _ensure_pool(force=False)

    available = [r for r in _POOL if r.get("ticker", "").upper() not in exclude]

    if len(available) < 10:
        _ensure_pool(force=True)
        available = [r for r in _POOL if r.get("ticker", "").upper() not in exclude]

    if len(available) < 5:
        _USER_SEEN[uid] = set()
        exclude = {t.upper() for t in portfolio_tickers} | {t.upper() for t in watchlist_tickers}
        available = [r for r in _POOL if r.get("ticker", "").upper() not in exclude]

    random.shuffle(available)
    results = []
    skipped_tickers = set()
    for rec in available:
        if len(results) >= 10:
            break
        try:
            enriched = _enrich_recommendation(rec, fast=False)
            if enriched.get("price", 0) <= 0:
                skipped_tickers.add(rec.get("ticker", ""))
                continue
            results.append(enriched)
        except Exception:
            skipped_tickers.add(rec.get("ticker", ""))
            continue

    if skipped_tickers:
        _POOL[:] = [r for r in _POOL if r.get("ticker", "") not in skipped_tickers]

    seen = _USER_SEEN.get(uid, set())
    seen |= {r.get("ticker", "").upper() for r in results}
    _USER_SEEN[uid] = seen

    return results


@router.post("/matchmaker")
async def matchmaker(user: CurrentUser, body: MatchmakerRequest):
    if user.role.lower() not in ("pro", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "PRO or ADMIN required")

    results = await asyncio.to_thread(
        _run_matchmaker, user.user_id, body.tickers, body.watchlist
    )
    return {"recommendations": results}


@router.post("/port-doctor")
async def port_doctor(user: CurrentUser, body: PortDoctorRequest):
    if user.role.lower() not in ("pro", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "PRO or ADMIN required")

    diagnosis = await asyncio.to_thread(generate_port_doctor_diagnosis, body.portfolio)
    return {"diagnosis": diagnosis}


@router.post("/rebalance")
async def rebalance(user: CurrentUser, body: RebalanceRequest):
    if user.role.lower() not in ("pro", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "PRO or ADMIN required")

    result = await asyncio.to_thread(generate_rebalance_strategy, body.portfolio)
    return {"strategy": result}


@router.post("/copilot")
async def copilot(user: CurrentUser, body: CopilotRequest):
    if user.role.lower() not in ("pro", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "PRO or ADMIN required")

    reply = await asyncio.to_thread(generate_copilot_reply, body.message, user.role.lower())
    return {"reply": reply}


def _build_morning_briefing() -> str:
    """Synchronous helper — runs in a thread pool."""
    try:
        fg_value, fg_text = get_real_fear_and_greed()
    except Exception:
        fg_value, fg_text = 0, "Unavailable"

    vix = get_live_price("^VIX") or 0.0

    try:
        sectors = get_real_sector_rotation()
        sector_summary = "\n".join(f"- {s['sector']}: {s['flow_pct']:+.2f}%" for s in sectors[:5])
    except Exception:
        sector_summary = "Sector data unavailable"

    market_summary = f"""
Fear & Greed Index: {fg_value} ({fg_text})
VIX: {vix:.2f}
Top Sector Flows:
{sector_summary}
"""
    return generate_morning_briefing(market_summary)


@router.post("/morning-briefing")
async def morning_briefing(user: CurrentUser):
    if user.role.lower() not in ("pro", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "PRO or ADMIN required")

    result = await asyncio.to_thread(_build_morning_briefing)
    return {"briefing": result}
