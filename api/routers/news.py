"""News endpoint — AI-summarized stock news for portfolio tickers."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter

from api.deps import CurrentUser
from core.models import get_portfolio
from services.news_fetcher import fetch_stock_news_summary

router = APIRouter(prefix="/api/news", tags=["news"])

_executor = ThreadPoolExecutor(max_workers=3)


@router.get("")
async def portfolio_news(user: CurrentUser):
    portfolio = get_portfolio(user.user_id)
    tickers = [s["ticker"] for s in portfolio]
    if not tickers:
        return {"news": []}

    sem = asyncio.Semaphore(3)
    loop = asyncio.get_event_loop()

    async def _fetch(ticker: str):
        async with sem:
            summary = await loop.run_in_executor(_executor, fetch_stock_news_summary, ticker)
            return {"ticker": ticker, "summary": summary}

    results = await asyncio.gather(*[_fetch(t) for t in tickers])
    return {"news": list(results)}
