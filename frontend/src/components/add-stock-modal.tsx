"use client";

import { useState } from "react";
import { X, Loader2 } from "lucide-react";
import api from "@/lib/api";

interface Props {
  open: boolean;
  onClose: () => void;
  onAdded: () => void;
}

export default function AddStockModal({ open, onClose, onAdded }: Props) {
  const [ticker, setTicker] = useState("");
  const [shares, setShares] = useState("");
  const [avgCost, setAvgCost] = useState("");
  const [group, setGroup] = useState("ALL");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!ticker.trim() || !shares || !avgCost) {
      setError("Please fill all fields");
      return;
    }
    setLoading(true);
    try {
      await api.post("/api/portfolio", {
        ticker: ticker.trim().toUpperCase(),
        shares: parseFloat(shares),
        avg_cost: parseFloat(avgCost),
        asset_group: group,
      });
      setTicker("");
      setShares("");
      setAvgCost("");
      onAdded();
      onClose();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Failed to add stock";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-[94vw] max-w-[440px] bg-[#0D1117] border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/8">
          <h2 className="text-lg font-black text-white tracking-wide">
            Add Stock
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-white p-1"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1 font-bold uppercase tracking-wider">
              Ticker
            </label>
            <input
              type="text"
              placeholder="AAPL"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-gray-600 outline-none focus:border-[#D0FD3E]/40"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1 font-bold uppercase tracking-wider">
                Shares
              </label>
              <input
                type="number"
                step="any"
                placeholder="10"
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
                placeholder="150.00"
                value={avgCost}
                onChange={(e) => setAvgCost(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-gray-600 outline-none focus:border-[#D0FD3E]/40"
              />
            </div>
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
            </select>
          </div>

          {error && (
            <p className="text-sm text-[#FF453A] bg-[#FF453A]/10 border border-[#FF453A]/20 rounded-xl p-2 text-center">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-[#D0FD3E] hover:bg-[#c5f232] text-[#080B10] font-black tracking-wider rounded-xl transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : "ADD"}
          </button>
        </form>
      </div>
    </div>
  );
}
