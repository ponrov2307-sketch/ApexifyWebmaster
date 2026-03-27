"""Price alerts endpoints — enhanced with current price and progress."""

import asyncio

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.deps import CurrentUser
from core.models import delete_price_alert, get_user_price_alerts, set_user_price_alert
from services.yahoo_finance import batch_get_prices, get_live_price

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    symbol: str
    target_price: float = Field(gt=0)
    condition: str = Field(pattern="^(above|below)$")


def _build_alerts_response(uid: str) -> list:
    """Synchronous helper — runs in a thread pool."""
    alerts = get_user_price_alerts(uid)
    if not alerts:
        return []

    # Batch fetch all prices in one yfinance call
    symbols = [a.get("symbol", "") for a in alerts]
    prices = batch_get_prices(symbols)

    enriched = []
    for a in alerts:
        symbol = a.get("symbol", "")
        target_price = a.get("target_price", 0)
        condition = a.get("condition", "above")
        current_price = prices.get(symbol, 0.0)

        progress = 0.0
        if condition == "above" and target_price > 0 and current_price > 0:
            if current_price >= target_price:
                progress = 100.0
            else:
                baseline = target_price * 0.8
                if current_price > baseline:
                    progress = min(99.0, ((current_price - baseline) / (target_price - baseline)) * 100)
                else:
                    progress = max(0, (current_price / target_price) * 100)
        elif condition == "below" and target_price > 0 and current_price > 0:
            if current_price <= target_price:
                progress = 100.0
            else:
                baseline = target_price * 1.2
                if current_price < baseline:
                    progress = min(99.0, ((baseline - current_price) / (baseline - target_price)) * 100)
                else:
                    progress = max(0, (target_price / current_price) * 100)

        distance_pct = ((target_price - current_price) / current_price * 100) if current_price > 0 else 0.0

        enriched.append({
            **a,
            "current_price": round(current_price, 2),
            "progress": round(progress, 1),
            "distance_pct": round(distance_pct, 2),
        })

    return enriched


@router.get("")
async def list_alerts(user: CurrentUser):
    enriched = await asyncio.to_thread(_build_alerts_response, user.user_id)
    return {"alerts": enriched}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_alert(user: CurrentUser, body: AlertCreate):
    if user.role.lower() == "free":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Upgrade to VIP or PRO to create price alerts")

    ok = await asyncio.to_thread(set_user_price_alert, user.user_id, body.symbol, body.target_price, body.condition)
    if not ok:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create alert")
    return {"ok": True, "symbol": body.symbol.upper()}


@router.delete("/{alert_id}")
async def remove_alert(alert_id: int, user: CurrentUser):
    ok = await asyncio.to_thread(delete_price_alert, alert_id)
    if not ok:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to delete alert")
    return {"ok": True}
