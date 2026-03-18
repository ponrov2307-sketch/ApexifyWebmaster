"""FastAPI application — serves REST API for the Next.js frontend."""

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import ai, alerts, auth, market, news, portfolio, watchlist


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: preload popular stock data in background thread
    from services.yahoo_finance import preload_popular_stocks
    t = threading.Thread(target=preload_popular_stocks, daemon=True)
    t.start()
    yield


app = FastAPI(
    title="Apexify API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai.router)
app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(market.router)
app.include_router(alerts.router)
app.include_router(news.router)
app.include_router(watchlist.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
