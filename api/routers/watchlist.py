"""Watchlist CRUD endpoints — enhanced with sparkline, change %, volume, and dividend data."""

import asyncio

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.deps import CurrentUser
from core.models import (
    get_user_watchlist,
    add_watchlist_item,
    remove_watchlist_item,
)
from services.yahoo_finance import batch_get_prices, get_sparkline_data, get_ticker_info

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

ROLE_LIMITS = {"free": 3, "vip": 10, "pro": 999, "admin": 999}


class WatchlistAdd(BaseModel):
    ticker: str


def _build_watchlist_response(tickers: list[str]) -> list:
    """Synchronous helper — runs in a thread pool."""
    if not tickers:
        return []

    prices = batch_get_prices(tickers)
    items = []
    for t in tickers:
        price = prices.get(t, 0.0)

        spark_result = get_sparkline_data(t, days=7)
        spark_values = spark_result[0] if spark_result else []
        change_pct = 0.0
        prev_close = 0.0
        if spark_values and len(spark_values) >= 2:
            prev_close = spark_values[-2] if spark_values[-2] > 0 else spark_values[0]
            if prev_close > 0:
                change_pct = ((price - prev_close) / prev_close) * 100

        info = get_ticker_info(t)

        items.append({
            "ticker": t,
            "name": info.get("name", t),
            "price": round(price, 2),
            "change_pct": round(change_pct, 2),
            "prev_close": round(prev_close, 2),
            "day_high": round(info.get("day_high", 0), 2),
            "day_low": round(info.get("day_low", 0), 2),
            "volume": info.get("volume", 0),
            "market_cap": info.get("market_cap", 0),
            "div_yield": round(info.get("div_yield", 0), 2),
            "sparkline": spark_values,
        })
    return items


@router.get("")
async def list_watchlist(user: CurrentUser):
    tickers = await asyncio.to_thread(get_user_watchlist, user.user_id)
    items = await asyncio.to_thread(_build_watchlist_response, tickers)
    return {"items": items}


@router.post("")
async def add_to_watchlist(user: CurrentUser, body: WatchlistAdd):
    role = user.role.lower()
    limit = ROLE_LIMITS.get(role, 3)
    current = await asyncio.to_thread(get_user_watchlist, user.user_id)
    if len(current) >= limit:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Watchlist limit reached ({limit}). Upgrade for more.",
        )
    ticker = body.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ticker required")
    if ticker in current:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already in watchlist")
    await asyncio.to_thread(add_watchlist_item, user.user_id, ticker)
    return {"ok": True}


@router.delete("/{ticker}")
async def remove_from_watchlist(user: CurrentUser, ticker: str):
    await asyncio.to_thread(remove_watchlist_item, user.user_id, ticker.upper())
    return {"ok": True}
