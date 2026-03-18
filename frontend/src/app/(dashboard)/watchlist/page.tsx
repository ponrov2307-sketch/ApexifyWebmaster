"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-store";
import { useLang, tr } from "@/lib/i18n";
import { logoUrl } from "@/lib/dashboard-helpers";
import api from "@/lib/api";
import Sparkline from "@/components/sparkline";
import ChartModal from "@/components/chart-modal";
import {
  Eye,
  Plus,
  Trash2,
  Loader2,
  Lock,
  TrendingUp,
  TrendingDown,
  CandlestickChart,
  DollarSign,
  BarChart3,
  ArrowUpDown,
} from "lucide-react";

interface WatchItem {
  ticker: string;
  name: string;
  price: number;
  change_pct: number;
  prev_close: number;
  day_high: number;
  day_low: number;
  volume: number;
  market_cap: number;
  div_yield: number;
  sparkline: number[];
}

const LIMITS: Record<string, number> = { free: 3, vip: 10, pro: 999, admin: 999 };

function fmtVol(n: number): string {
  if (n >= 1e9) return (n / 1e9).toFixed(1) + "B";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return String(n);
}

function fmtMcap(n: number): string {
  if (n >= 1e12) return "$" + (n / 1e12).toFixed(2) + "T";
  if (n >= 1e9) return "$" + (n / 1e9).toFixed(1) + "B";
  if (n >= 1e6) return "$" + (n / 1e6).toFixed(0) + "M";
  return "$" + n.toLocaleString();
}

type SortKey = "ticker" | "price" | "change_pct" | "div_yield" | "volume";

export default function WatchlistPage() {
  const user = useAuth((s) => s.user);
  const { lang } = useLang();
  const role = (user?.role || "free").toLowerCase();
  const limit = LIMITS[role] ?? 3;

  const [items, setItems] = useState<WatchItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [newTicker, setNewTicker] = useState("");
  const [error, setError] = useState("");
  const [chartTicker, setChartTicker] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("ticker");
  const [sortAsc, setSortAsc] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/api/watchlist");
      setItems(data.items || []);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const iv = setInterval(refresh, 30000);
    return () => clearInterval(iv);
  }, [refresh]);

  const handleAdd = async () => {
    const t = newTicker.trim().toUpperCase();
    if (!t) return;
    if (items.length >= limit) {
      setError(
        lang === "TH"
          ? `แพ็กเกจของคุณรองรับ Watchlist ได้สูงสุด ${limit} ตัว`
          : `Your plan supports up to ${limit} watchlist items`,
      );
      return;
    }
    setAdding(true);
    setError("");
    try {
      await api.post("/api/watchlist", { ticker: t });
      setNewTicker("");
      await refresh();
    } catch {
      setError(lang === "TH" ? "ไม่สามารถเพิ่มได้" : "Failed to add ticker");
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (ticker: string) => {
    try {
      await api.delete(`/api/watchlist/${ticker}`);
      await refresh();
    } catch {
      /* ignore */
    }
  };

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(key === "ticker");
    }
  };

  const sorted = [...items].sort((a, b) => {
    const dir = sortAsc ? 1 : -1;
    if (sortKey === "ticker") return a.ticker.localeCompare(b.ticker) * dir;
    return ((a[sortKey] || 0) - (b[sortKey] || 0)) * dir;
  });

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-black tracking-wide flex items-center gap-3" style={{ color: 'var(--text-primary)' }}>
          <Eye className="text-[#56D3FF]" size={24} />
          {tr("watchlist.title", lang)}
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
          {tr("watchlist.subtitle", lang)} ·{" "}
          <span className="text-[#56D3FF] font-bold">
            {items.length}/{limit === 999 ? "∞" : limit}
          </span>
        </p>
      </div>

      {/* Add ticker */}
      <div className="border rounded-2xl p-4 mb-4" style={{ background: 'var(--bg-card)', borderColor: 'var(--border-default)' }}>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder={lang === "TH" ? "เช่น AAPL, TSLA, PTT.BK" : "e.g. AAPL, TSLA, PTT.BK"}
            value={newTicker}
            onChange={(e) => setNewTicker(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            className="flex-1 border rounded-xl px-4 py-2.5 placeholder:text-gray-500 outline-none focus:border-[#56D3FF]/40 uppercase text-sm"
            style={{ background: 'var(--input-bg)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }}
          />
          <button
            onClick={handleAdd}
            disabled={adding || items.length >= limit}
            className="flex items-center gap-1.5 px-5 py-2.5 bg-[#56D3FF] text-black font-black rounded-xl text-sm disabled:opacity-50 transition-colors hover:bg-[#3dc0f0]"
          >
            {adding ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
            {tr("watchlist.add", lang)}
          </button>
        </div>
        {error && <p className="text-sm text-[#FF453A] mt-2">{error}</p>}
        {items.length >= limit && limit < 999 && (
          <div className="flex items-center gap-2 mt-3 text-[#FFD700] text-xs">
            <Lock size={12} />
            <span>
              {lang === "TH"
                ? "ถึงขีดจำกัดแล้ว อัปเกรดเพื่อเพิ่มเพิ่มเติม"
                : "Limit reached. Upgrade for more slots."}
            </span>
          </div>
        )}
      </div>

      {/* List */}
      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-[#56D3FF]" />
        </div>
      ) : items.length === 0 ? (
        <div className="border rounded-2xl p-12 text-center" style={{ background: 'var(--bg-card)', borderColor: 'var(--border-default)' }}>
          <Eye className="w-12 h-12 text-gray-700 mx-auto mb-4" />
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {lang === "TH" ? "ยังไม่มี Watchlist" : "Your watchlist is empty"}
          </p>
        </div>
      ) : (
        <>
          {/* Sort controls */}
          <div className="flex items-center gap-2 mb-3 text-xs font-bold" style={{ color: 'var(--text-muted)' }}>
            <ArrowUpDown size={12} />
            <span>{lang === "TH" ? "เรียง:" : "Sort:"}</span>
            {([
              { key: "ticker" as SortKey, label: "Name" },
              { key: "price" as SortKey, label: "Price" },
              { key: "change_pct" as SortKey, label: "Change" },
              { key: "div_yield" as SortKey, label: "Dividend" },
              { key: "volume" as SortKey, label: "Volume" },
            ]).map(s => (
              <button
                key={s.key}
                onClick={() => toggleSort(s.key)}
                className={`px-2 py-0.5 rounded-lg transition-colors ${
                  sortKey === s.key ? "bg-[#56D3FF]/20 text-[#56D3FF]" : "hover:bg-white/5"
                }`}
              >
                {s.label} {sortKey === s.key && (sortAsc ? "↑" : "↓")}
              </button>
            ))}
          </div>

          {/* Cards */}
          <div className="space-y-2">
            {sorted.map((item) => {
              const up = item.change_pct >= 0;
              const isSparkUp = item.sparkline?.length > 1 ? item.sparkline[item.sparkline.length - 1] >= item.sparkline[0] : up;
              const dayRange = item.day_high > 0 ? ((item.price - item.day_low) / (item.day_high - item.day_low)) * 100 : 50;

              return (
                <div
                  key={item.ticker}
                  className="group border hover:border-opacity-30 rounded-2xl p-4 transition-all"
                  style={{ background: 'var(--bg-card)', borderColor: 'var(--border-default)' }}
                >
                  {/* Top row: Logo + Name + Sparkline + Price */}
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-[180px]">
                      <img
                        src={logoUrl(item.ticker)}
                        alt=""
                        className="w-10 h-10 rounded-full border"
                        style={{ borderColor: 'var(--border-default)', background: 'var(--bg-surface)' }}
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${item.ticker}&background=1a1f26&color=fff&bold=true&size=40`;
                        }}
                      />
                      <div>
                        <p className="text-lg font-black" style={{ color: 'var(--text-primary)' }}>{item.ticker}</p>
                        <p className="text-xs truncate max-w-[140px]" style={{ color: 'var(--text-muted)' }}>{item.name}</p>
                      </div>
                    </div>

                    {/* Sparkline */}
                    <div className="flex-1 flex items-center justify-center h-12 min-w-[100px] max-w-[180px]">
                      {item.sparkline?.length > 1 && (
                        <Sparkline data={item.sparkline} width={150} height={40} positive={isSparkUp} />
                      )}
                    </div>

                    {/* Price + Change */}
                    <div className="flex items-center gap-4 min-w-[200px] justify-end">
                      <div className="text-right">
                        <p className="text-lg font-black tabular-nums" style={{ color: 'var(--text-primary)' }}>
                          ${item.price.toFixed(2)}
                        </p>
                        <div className="flex items-center gap-1 justify-end">
                          {up ? (
                            <TrendingUp size={12} className="text-[#32D74B]" />
                          ) : (
                            <TrendingDown size={12} className="text-[#FF453A]" />
                          )}
                          <span
                            className="text-sm font-black tabular-nums"
                            style={{ color: up ? "#32D74B" : "#FF453A" }}
                          >
                            {up ? "+" : ""}{item.change_pct.toFixed(2)}%
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setChartTicker(item.ticker)}
                          className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          <CandlestickChart size={16} />
                        </button>
                        <button
                          onClick={() => handleRemove(item.ticker)}
                          className="text-gray-500 hover:text-[#FF453A] p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Bottom row: Stats */}
                  <div className="flex flex-wrap items-center gap-3 mt-3 pt-3" style={{ borderTop: '1px solid var(--border-subtle)' }}>
                    {/* Day Range */}
                    <div className="flex items-center gap-2 min-w-[160px]">
                      <span className="text-[10px] font-bold" style={{ color: 'var(--text-dim)' }}>DAY</span>
                      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--input-bg)' }}>
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${Math.max(2, Math.min(100, dayRange))}%`,
                            background: up ? '#32D74B' : '#FF453A',
                          }}
                        />
                      </div>
                      <span className="text-[10px] tabular-nums" style={{ color: 'var(--text-dim)' }}>
                        {item.day_low > 0 ? `${item.day_low.toFixed(2)}-${item.day_high.toFixed(2)}` : "—"}
                      </span>
                    </div>

                    {/* Volume */}
                    <div className="flex items-center gap-1.5">
                      <BarChart3 size={10} style={{ color: 'var(--text-dim)' }} />
                      <span className="text-[10px] font-bold" style={{ color: 'var(--text-dim)' }}>VOL</span>
                      <span className="text-xs font-bold tabular-nums" style={{ color: 'var(--text-secondary)' }}>
                        {item.volume > 0 ? fmtVol(item.volume) : "—"}
                      </span>
                    </div>

                    {/* Market Cap */}
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-bold" style={{ color: 'var(--text-dim)' }}>MCAP</span>
                      <span className="text-xs font-bold tabular-nums" style={{ color: 'var(--text-secondary)' }}>
                        {item.market_cap > 0 ? fmtMcap(item.market_cap) : "—"}
                      </span>
                    </div>

                    {/* Dividend Yield */}
                    {item.div_yield > 0 && (
                      <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-[#32D74B]/10">
                        <DollarSign size={10} className="text-[#32D74B]" />
                        <span className="text-[10px] font-black text-[#32D74B] tabular-nums">
                          DIV {item.div_yield.toFixed(2)}%
                        </span>
                      </div>
                    )}

                    {/* Prev Close */}
                    {item.prev_close > 0 && (
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-bold" style={{ color: 'var(--text-dim)' }}>PREV</span>
                        <span className="text-xs tabular-nums" style={{ color: 'var(--text-muted)' }}>
                          ${item.prev_close.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {chartTicker && (
        <ChartModal ticker={chartTicker} open={true} onClose={() => setChartTicker(null)} />
      )}
    </div>
  );
}
