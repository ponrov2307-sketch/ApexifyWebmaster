"use client";

import { useState } from "react";
import { useAlerts } from "@/lib/hooks";
import { logoUrl } from "@/lib/dashboard-helpers";
import api from "@/lib/api";
import {
  Bell,
  Plus,
  Trash2,
  ArrowUp,
  ArrowDown,
  Loader2,
  BellOff,
  Target,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import ProGate from "@/components/pro-gate";

export default function AlertsPage() {
  const { alerts, loading, refresh } = useAlerts();
  const [showForm, setShowForm] = useState(false);
  const [symbol, setSymbol] = useState("");
  const [price, setPrice] = useState("");
  const [condition, setCondition] = useState<"above" | "below">("above");
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [error, setError] = useState("");

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!symbol.trim() || !price) {
      setError("Fill all fields");
      return;
    }
    setCreating(true);
    try {
      await api.post("/api/alerts", {
        symbol: symbol.trim().toUpperCase(),
        target_price: parseFloat(price),
        condition,
      });
      setSymbol("");
      setPrice("");
      setShowForm(false);
      await refresh();
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Failed",
      );
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    setDeleting(id);
    try {
      await api.delete(`/api/alerts/${id}`);
      await refresh();
    } catch {
      /* ignore */
    } finally {
      setDeleting(null);
    }
  };

  return (
    <ProGate>
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-black tracking-wide flex items-center gap-3" style={{ color: 'var(--text-primary)' }}>
            <Bell className="text-[#FCD535]" size={24} />
            Price Alerts
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            Get notified when a stock hits your target price
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1.5 px-4 py-2 bg-[#D0FD3E] text-[#080B10] font-bold rounded-xl text-sm hover:bg-[#c5f232] transition-colors"
        >
          <Plus size={14} />
          New Alert
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="border rounded-2xl p-5 mb-6" style={{ background: 'var(--bg-card)', borderColor: 'var(--border-default)' }}>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs mb-1 font-bold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                  Symbol
                </label>
                <input
                  type="text"
                  placeholder="AAPL"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  className="w-full border rounded-xl px-4 py-2.5 placeholder:text-gray-600 outline-none focus:border-[#D0FD3E]/40"
                  style={{ background: 'var(--input-bg)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }}
                />
              </div>
              <div>
                <label className="block text-xs mb-1 font-bold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                  Target Price ($)
                </label>
                <input
                  type="number"
                  step="any"
                  placeholder="200.00"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  className="w-full border rounded-xl px-4 py-2.5 placeholder:text-gray-600 outline-none focus:border-[#D0FD3E]/40"
                  style={{ background: 'var(--input-bg)', borderColor: 'var(--border-default)', color: 'var(--text-primary)' }}
                />
              </div>
              <div>
                <label className="block text-xs mb-1 font-bold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                  Condition
                </label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setCondition("above")}
                    className={`flex-1 flex items-center justify-center gap-1 py-2.5 rounded-xl text-sm font-bold transition-colors ${
                      condition === "above"
                        ? "bg-[#32D74B]/20 border border-[#32D74B]/40 text-[#32D74B]"
                        : "border text-gray-400"
                    }`}
                    style={condition !== "above" ? { background: 'var(--input-bg)', borderColor: 'var(--border-default)' } : {}}
                  >
                    <ArrowUp size={14} />
                    Above
                  </button>
                  <button
                    type="button"
                    onClick={() => setCondition("below")}
                    className={`flex-1 flex items-center justify-center gap-1 py-2.5 rounded-xl text-sm font-bold transition-colors ${
                      condition === "below"
                        ? "bg-[#FF453A]/20 border border-[#FF453A]/40 text-[#FF453A]"
                        : "border text-gray-400"
                    }`}
                    style={condition !== "below" ? { background: 'var(--input-bg)', borderColor: 'var(--border-default)' } : {}}
                  >
                    <ArrowDown size={14} />
                    Below
                  </button>
                </div>
              </div>
            </div>
            {error && (
              <p className="text-sm text-[#FF453A]">{error}</p>
            )}
            <button
              type="submit"
              disabled={creating}
              className="w-full sm:w-auto px-6 py-2.5 bg-[#D0FD3E] text-[#080B10] font-black rounded-xl text-sm hover:bg-[#c5f232] disabled:opacity-50 flex items-center gap-2"
            >
              {creating ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                "Create Alert"
              )}
            </button>
          </form>
        </div>
      )}

      {/* Alerts list */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
        </div>
      ) : alerts.length === 0 ? (
        <div className="border rounded-2xl p-12 text-center" style={{ background: 'var(--bg-card)', borderColor: 'var(--border-default)' }}>
          <BellOff className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h2 className="text-lg font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
            No alerts yet
          </h2>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Create your first price alert to get notified via Telegram
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((a) => {
            const isAbove = a.condition === "above";
            const accentColor = isAbove ? "#32D74B" : "#FF453A";
            const currentPrice = a.current_price || 0;
            const progress = a.progress || 0;
            const distancePct = a.distance_pct || 0;
            const priceUp = currentPrice > 0 && a.target_price > 0 && currentPrice >= a.target_price;

            return (
              <div
                key={a.id}
                className="border rounded-2xl p-5 transition-colors group"
                style={{ background: 'var(--bg-card)', borderColor: 'var(--border-default)' }}
              >
                {/* Top row */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <img
                      src={logoUrl(a.symbol)}
                      alt=""
                      className="w-10 h-10 rounded-full border"
                      style={{ borderColor: 'var(--border-default)', background: 'var(--bg-surface)' }}
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${a.symbol}&background=1a1f26&color=fff&bold=true&size=40`;
                      }}
                    />
                    <div>
                      <span className="font-black text-xl" style={{ color: 'var(--text-primary)' }}>
                        {a.symbol}
                      </span>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="font-bold px-1.5 py-0.5 rounded" style={{ color: accentColor, background: `${accentColor}15` }}>
                          {isAbove ? "▲ Above" : "▼ Below"}
                        </span>
                        <span className="font-mono font-bold" style={{ color: 'var(--text-primary)' }}>
                          ${a.target_price.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDelete(a.id)}
                    disabled={deleting === a.id}
                    className="opacity-0 group-hover:opacity-100 hover:text-[#FF453A] transition-all p-2 rounded-lg hover:bg-[#FF453A]/10"
                    style={{ color: 'var(--text-dim)' }}
                  >
                    {deleting === a.id ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Trash2 size={16} />
                    )}
                  </button>
                </div>

                {/* Progress bar section */}
                <div className="space-y-2">
                  {/* Current price and distance */}
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span style={{ color: 'var(--text-muted)' }}>Current:</span>
                      <span className="font-black tabular-nums" style={{ color: 'var(--text-primary)' }}>
                        ${currentPrice.toFixed(2)}
                      </span>
                      {currentPrice > 0 && (
                        <span className="flex items-center gap-0.5 font-bold tabular-nums" style={{ color: distancePct >= 0 ? "#32D74B" : "#FF453A" }}>
                          {distancePct >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                          {distancePct >= 0 ? "+" : ""}{distancePct.toFixed(2)}% to target
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <Target size={10} style={{ color: accentColor }} />
                      <span className="font-black tabular-nums" style={{ color: accentColor }}>
                        {progress.toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="relative h-3 rounded-full overflow-hidden" style={{ background: 'var(--input-bg)' }}>
                    <div
                      className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.max(2, Math.min(100, progress))}%`,
                        background: `linear-gradient(90deg, ${accentColor}80, ${accentColor})`,
                        boxShadow: progress > 50 ? `0 0 12px ${accentColor}60` : 'none',
                      }}
                    />
                    {/* Target marker */}
                    <div
                      className="absolute top-0 bottom-0 w-0.5"
                      style={{ left: '100%', transform: 'translateX(-2px)', background: accentColor }}
                    />
                  </div>

                  {/* Price scale */}
                  <div className="flex items-center justify-between text-[10px] tabular-nums" style={{ color: 'var(--text-dim)' }}>
                    <span>${(currentPrice * 0.8).toFixed(0)}</span>
                    <span className="font-bold" style={{ color: 'var(--text-muted)' }}>
                      ${currentPrice.toFixed(2)}
                    </span>
                    <span className="font-bold" style={{ color: accentColor }}>
                      ${a.target_price.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
    </ProGate>
  );
}
