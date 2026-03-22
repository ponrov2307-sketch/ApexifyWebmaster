"use client";

import { useState, useEffect } from "react";
import { X, Loader2, Trash2, Shield, TrendingUp } from "lucide-react";
import api from "@/lib/api";

interface Props {
  ticker: string;
  shares: number;
  avgCost: number;
  alertPrice: number;
  assetGroup: string;
  currentPrice: number;
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export default function EditStockModal({
  ticker,
  shares: initShares,
  avgCost: initAvgCost,
  alertPrice: initAlertPrice,
  assetGroup: initGroup,
  currentPrice,
  open,
  onClose,
  onSaved,
}: Props) {
  const [shares, setShares] = useState(initShares.toString());
  const [avgCost, setAvgCost] = useState(initAvgCost.toString());
  const [alertPriceVal, setAlertPriceVal] = useState(initAlertPrice.toString());
  const [group, setGroup] = useState(initGroup);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");
  const [support, setSupport] = useState<number[]>([]);
  const [resistance, setResistance] = useState<number[]>([]);

  useEffect(() => {
    if (open) {
      setShares(initShares.toString());
      setAvgCost(initAvgCost.toString());
      setAlertPriceVal(initAlertPrice.toString());
      setGroup(initGroup);
      setError("");
      // Fetch support/resistance
      api
        .get(`/api/market/support-resistance/${ticker}`)
        .then(({ data }) => {
          setSupport(data.support || []);
          setResistance(data.resistance || []);
        })
        .catch(() => {});
    }
  }, [open, ticker, initShares, initAvgCost, initAlertPrice, initGroup]);

  if (!open) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!shares || !avgCost) {
      setError("Shares and Avg Cost are required");
      return;
    }
    setSaving(true);
    try {
      await api.put(`/api/portfolio/${ticker}`, {
        shares: parseFloat(shares),
        avg_cost: parseFloat(avgCost),
        asset_group: group,
        alert_price: parseFloat(alertPriceVal) || 0,
      });
      onSaved();
      onClose();
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Failed to save",
      );
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Remove ${ticker} from portfolio?`)) return;
    setDeleting(true);
    try {
      await api.delete(`/api/portfolio/${ticker}`);
      onSaved();
      onClose();
    } catch {
      setError("Failed to delete");
    } finally {
      setDeleting(false);
    }
  };

  const pnl = (currentPrice - parseFloat(avgCost || "0")) * parseFloat(shares || "0");
  const pnlPct = parseFloat(avgCost || "0") > 0 ? ((currentPrice - parseFloat(avgCost || "0")) / parseFloat(avgCost || "0")) * 100 : 0;
  const up = pnl >= 0;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-[94vw] max-w-[480px] bg-[#0D1117] border border-white/10 rounded-2xl overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-sm font-black text-white">
              {ticker.slice(0, 2)}
            </div>
            <div>
              <h2 className="text-lg font-black text-white tracking-wide">
                {ticker}
              </h2>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-400">
                  ${currentPrice.toFixed(2)}
                </span>
                <span
                  className="font-bold text-xs"
                  style={{ color: up ? "#32D74B" : "#FF453A" }}
                >
                  {up ? "+" : ""}
                  {pnlPct.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-white p-1"
          >
            <X size={20} />
          </button>
        </div>

        {/* Support/Resistance */}
        {(support.length > 0 || resistance.length > 0) && (
          <div className="px-5 py-2.5 border-b border-white/5 flex gap-4 text-xs">
            {support.length > 0 && (
              <div className="flex items-center gap-1.5">
                <Shield size={12} className="text-[#32D74B]" />
                <span className="text-gray-500">Support:</span>
                <span className="text-[#32D74B] font-mono font-bold">
                  ${support[0]?.toFixed(2)}
                </span>
              </div>
            )}
            {resistance.length > 0 && (
              <div className="flex items-center gap-1.5">
                <TrendingUp size={12} className="text-[#FF453A]" />
                <span className="text-gray-500">Resistance:</span>
                <span className="text-[#FF453A] font-mono font-bold">
                  ${resistance[0]?.toFixed(2)}
                </span>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSave} className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1 font-bold uppercase tracking-wider">
                Shares
              </label>
              <input
                type="number"
                step="any"
                value={shares}
                onChange={(e) => setShares(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-gray-600 outline-none focus:border-[#D0FD3E]/40"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1 font-bold uppercase tracking-wider">
                Avg Cost ($)
              </label>
              <input
                type="number"
                step="any"
                value={avgCost}
                onChange={(e) => setAvgCost(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-gray-600 outline-none focus:border-[#D0FD3E]/40"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1 font-bold uppercase tracking-wider">
                Price Alert ($)
              </label>
              <input
                type="number"
                step="any"
                value={alertPriceVal}
                onChange={(e) => setAlertPriceVal(e.target.value)}
                placeholder="0.00"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-gray-600 outline-none focus:border-[#D0FD3E]/40"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1 font-bold uppercase tracking-wider">
                Group
              </label>
              <select
                value={group}
                onChange={(e) => setGroup(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white outline-none focus:border-[#D0FD3E]/40"
                style={{ backgroundColor: "#0D1117", color: "#FFFFFF", colorScheme: "dark" }}
              >
                <option value="ALL" style={{ backgroundColor: "#0D1117", color: "#FFFFFF" }}>ALL</option>
                <option value="DCA" style={{ backgroundColor: "#0D1117", color: "#FFFFFF" }}>DCA</option>
                <option value="DIV" style={{ backgroundColor: "#0D1117", color: "#FFFFFF" }}>DIV</option>
                <option value="TRADING" style={{ backgroundColor: "#0D1117", color: "#FFFFFF" }}>TRADING</option>
                <option value="TECH" style={{ backgroundColor: "#0D1117", color: "#FFFFFF" }}>TECH</option>
                <option value="FINANCE" style={{ backgroundColor: "#0D1117", color: "#FFFFFF" }}>FINANCE</option>
                <option value="ENERGY" style={{ backgroundColor: "#0D1117", color: "#FFFFFF" }}>ENERGY</option>
                <option value="ETF" style={{ backgroundColor: "#0D1117", color: "#FFFFFF" }}>ETF</option>
                <option value="CRYPTO" style={{ backgroundColor: "#0D1117", color: "#FFFFFF" }}>CRYPTO</option>
              </select>
            </div>
          </div>

          {/* P&L Preview */}
          <div className="bg-white/5 rounded-xl p-3 flex items-center justify-between">
            <span className="text-xs text-gray-500 font-bold">
              Unrealized P&L
            </span>
            <span
              className="font-mono font-bold"
              style={{ color: up ? "#32D74B" : "#FF453A" }}
            >
              {up ? "+" : ""}${pnl.toFixed(2)} ({up ? "+" : ""}
              {pnlPct.toFixed(2)}%)
            </span>
          </div>

          {error && (
            <p className="text-sm text-[#FF453A] bg-[#FF453A]/10 border border-[#FF453A]/20 rounded-xl p-2 text-center">
              {error}
            </p>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleDelete}
              disabled={deleting}
              className="px-4 py-3 bg-[#FF453A]/10 border border-[#FF453A]/20 text-[#FF453A] font-bold rounded-xl hover:bg-[#FF453A]/20 transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {deleting ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Trash2 size={16} />
              )}
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-3 bg-[#D0FD3E] hover:bg-[#c5f232] text-[#080B10] font-black tracking-wider rounded-xl transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {saving ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                "Save & Sync"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
