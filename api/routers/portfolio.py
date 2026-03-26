"""Portfolio CRUD endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.deps import CurrentUser
from core.models import (
    add_portfolio_stock,
    delete_portfolio_stock,
    get_portfolio,
    update_portfolio_stock,
)
from services.yahoo_finance import get_live_price, get_real_dividend_data, get_sparkline_data, get_usd_thb_rate, batch_get_prices

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


class StockAdd(BaseModel):
    ticker: str
    shares: float = Field(gt=0)
    avg_cost: float = Field(gt=0)
    asset_group: str = "ALL"


class StockUpdate(BaseModel):
    shares: float = Field(gt=0)
    avg_cost: float = Field(gt=0)
    asset_group: str = "ALL"
    alert_price: float = 0.0


def _build_portfolio_response(portfolio: list, currency: str) -> dict:
    """Synchronous helper — safe to run in a thread."""
    actual_thb_rate = get_usd_thb_rate()
    thb_rate = actual_thb_rate if currency == "THB" else 1.0

    # Batch fetch all prices in ONE yfinance call (much faster than N individual calls)
    tickers = [s["ticker"] for s in portfolio]
    prices = batch_get_prices(tickers)

    items = []
    total_value = 0.0
    total_cost = 0.0

    for stock in portfolio:
        ticker = stock["ticker"]
        shares = stock["shares"]
        avg_cost = stock["avg_cost"]

        price = prices.get(ticker, 0.0)
        value = price * shares
        cost = avg_cost * shares
        pnl = value - cost
        pnl_pct = (pnl / cost * 100) if cost > 0 else 0.0

        spark_result = get_sparkline_data(ticker, days=7)
        spark_values = spark_result[0] if spark_result else []

        items.append({
            "ticker": ticker,
            "shares": shares,
            "avg_cost": round(avg_cost * thb_rate, 2),
            "price": round(price * thb_rate, 2),
            "value": round(value * thb_rate, 2),
            "cost": round(cost * thb_rate, 2),
            "pnl": round(pnl * thb_rate, 2),
            "pnl_pct": round(pnl_pct, 2),
            "asset_group": stock.get("asset_group", "ALL"),
            "alert_price": stock.get("alert_price", 0.0),
            "sparkline": spark_values,
        })

        total_value += value
        total_cost += cost

    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0

    return {
        "items": items,
        "summary": {
            "total_value": round(total_value * thb_rate, 2),
            "total_cost": round(total_cost * thb_rate, 2),
            "total_pnl": round(total_pnl * thb_rate, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "currency": currency,
            "thb_rate": round(actual_thb_rate, 4),
        },
    }


@router.get("")
async def list_portfolio(user: CurrentUser, currency: str = "USD"):
    import asyncio

    portfolio = get_portfolio(user.user_id)
    if not portfolio:
        return {"items": [], "summary": {"total_value": 0, "total_cost": 0, "total_pnl": 0, "total_pnl_pct": 0}}

    try:
        return await asyncio.to_thread(_build_portfolio_response, portfolio, currency)
    except Exception:
        # Fallback: return empty rather than 500
        return {"items": [], "summary": {"total_value": 0, "total_cost": 0, "total_pnl": 0, "total_pnl_pct": 0}}


STOCK_LIMITS = {"free": 3, "vip": 10}  # pro/admin = unlimited


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_stock(user: CurrentUser, body: StockAdd):
    role = user.role.lower()
    limit = STOCK_LIMITS.get(role)
    if limit is not None:
        current = get_portfolio(user.user_id) or []
        if len(current) >= limit:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"{role.upper()} can hold max {limit} stocks. Upgrade to unlock more!",
            )

    ok = add_portfolio_stock(
        user.user_id, body.ticker, body.shares, body.avg_cost, body.asset_group
    )
    if not ok:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to add stock")
    return {"ok": True, "ticker": body.ticker.upper().strip()}


@router.put("/{ticker}")
async def update_stock(ticker: str, user: CurrentUser, body: StockUpdate):
    ok = update_portfolio_stock(
        user.user_id, ticker, body.shares, body.avg_cost, body.asset_group, body.alert_price
    )
    if not ok:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to update stock")
    return {"ok": True, "ticker": ticker.upper()}


@router.delete("/{ticker}")
async def remove_stock(ticker: str, user: CurrentUser):
    ok = delete_portfolio_stock(user.user_id, ticker)
    if not ok:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to delete stock")
    return {"ok": True, "ticker": ticker.upper()}


@router.get("/dividends")
async def portfolio_dividends(user: CurrentUser, currency: str = "USD"):
    portfolio = get_portfolio(user.user_id)
    if not portfolio:
        return {"items": [], "summary": {"total_annual": 0, "total_monthly": 0, "avg_yield": 0}}

    tickers = [s["ticker"] for s in portfolio]
    div_data = get_real_dividend_data(tickers)
    thb_rate = get_usd_thb_rate() if currency == "THB" else 1.0

    items = []
    total_annual = 0.0

    for stock in portfolio:
        ticker = stock["ticker"]
        shares = stock["shares"]
        price = get_live_price(ticker) or 0.0
        value = price * shares

        info = div_data.get(ticker, {})
        div_yield = info.get("yield", 0)
        amount_per_share = info.get("amount_per_share", 0)
        ex_date = info.get("ex_date", "N/A")

        annual_div = value * (div_yield / 100) if div_yield > 0 else 0
        monthly_div = annual_div / 12

        items.append({
            "ticker": ticker,
            "shares": shares,
            "price": round(price * thb_rate, 2),
            "value": round(value * thb_rate, 2),
            "div_yield": round(div_yield, 2),
            "amount_per_share": round(amount_per_share, 4),
            "annual_div": round(annual_div * thb_rate, 2),
            "monthly_div": round(monthly_div * thb_rate, 2),
            "ex_date": ex_date,
        })
        total_annual += annual_div

    total_monthly = total_annual / 12
    avg_yield = (sum(i["div_yield"] for i in items) / len(items)) if items else 0

    return {
        "items": items,
        "summary": {
            "total_annual": round(total_annual * thb_rate, 2),
            "total_monthly": round(total_monthly * thb_rate, 2),
            "avg_yield": round(avg_yield, 2),
            "currency": currency,
        },
    }
