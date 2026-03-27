import { useEffect, useState, useCallback, useRef } from "react";
import api from "./api";

// ─── Portfolio ───
export interface PortfolioItem {
  ticker: string;
  shares: number;
  avg_cost: number;
  price: number;
  value: number;
  cost: number;
  pnl: number;
  pnl_pct: number;
  asset_group: string;
  alert_price: number;
  sparkline: number[];
}

export interface PortfolioSummary {
  total_value: number;
  total_cost: number;
  total_pnl: number;
  total_pnl_pct: number;
  currency: string;
  thb_rate: number;
}

export function usePortfolio(currency: string = "USD", autoRefreshMs: number = 120000) {
  const [items, setItems] = useState<PortfolioItem[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const hasLoaded = useRef(false);

  const refresh = useCallback(async () => {
    // Only show loading spinner on first load, not on currency switch
    if (!hasLoaded.current) setLoading(true);
    setError("");
    try {
      const { data } = await api.get(`/api/portfolio?currency=${currency}`);
      setItems(data.items);
      setSummary(data.summary);
      hasLoaded.current = true;
    } catch {
      setError("Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  }, [currency]);

  // Silent refresh (no loading spinner)
  const silentRefresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/api/portfolio?currency=${currency}`);
      setItems(data.items);
      setSummary(data.summary);
    } catch {
      /* silent fail on auto-refresh */
    }
  }, [currency]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Auto-refresh interval for real-time prices
  useEffect(() => {
    if (autoRefreshMs > 0) {
      intervalRef.current = setInterval(silentRefresh, autoRefreshMs);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [silentRefresh, autoRefreshMs]);

  return { items, summary, loading, error, refresh };
}

// ─── Alerts ───
export interface Alert {
  id: number;
  symbol: string;
  target_price: number;
  condition: string;
  current_price: number;
  progress: number;
  distance_pct: number;
}

export function useAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/api/alerts");
      setAlerts(data.alerts || []);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { alerts, loading, refresh };
}

// ─── Market Summary ───
export interface IndexData {
  name: string;
  price: number;
}

export function useMarketSummary() {
  const [indices, setIndices] = useState<Record<string, IndexData>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/api/market/summary")
      .then(({ data }) => setIndices(data.indices || {}))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return { indices, loading };
}

// ─── Macro Data ───
export interface MacroData {
  fear_greed: { value: number; text: string };
  vix: number;
  indices: Record<string, { name: string; price: number }>;
  sectors: Record<string, number>;
}

export function useMacro() {
  const [data, setData] = useState<MacroData | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const { data: res } = await api.get("/api/market/macro");
      setData(res);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, refresh };
}

// ─── News ───
export interface NewsItem {
  ticker: string;
  summary: string;
}

export function useNews() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/api/news")
      .then(({ data }) => setNews(data.news || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return { news, loading };
}
