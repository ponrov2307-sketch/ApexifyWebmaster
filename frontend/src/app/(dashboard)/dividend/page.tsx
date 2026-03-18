"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import ProGate from "@/components/pro-gate";
import {
  DollarSign,
  Loader2,
  TrendingUp,
  Calendar,
  Percent,
  PiggyBank,
  RefreshCw,
} from "lucide-react";

function fmt(n: number) {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

interface DividendItem {
  ticker: string;
  shares: number;
  price: number;
  value: number;
  div_yield: number;
  amount_per_share: number;
  annual_div: number;
  monthly_div: number;
  ex_date: string;
}

interface DividendSummary {
  total_annual: number;
  total_monthly: number;
  avg_yield: number;
  currency: string;
}

export default function DividendPage() {
  const [items, setItems] = useState<DividendItem[]>([]);
  const [summary, setSummary] = useState<DividendSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/api/portfolio/dividends");
      setItems(data.items || []);
      setSummary(data.summary || null);
    } catch {
      setError("Failed to load dividend data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <ProGate>
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-black text-white tracking-wide flex items-center gap-3">
            <DollarSign className="text-[#32D74B]" size={24} />
            Dividend Tracker
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Real-time dividend income from your portfolio
          </p>
        </div>
        <button
          onClick={refresh}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
        </div>
      ) : error ? (
        <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-12 text-center">
          <DollarSign className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h2 className="text-lg font-bold text-white mb-2">{error}</h2>
          <button onClick={refresh} className="mt-4 px-4 py-2 bg-white/5 text-gray-300 rounded-xl text-sm hover:bg-white/10">
            Try Again
          </button>
        </div>
      ) : items.length === 0 ? (
        <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-12 text-center">
          <DollarSign className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h2 className="text-lg font-bold text-white mb-2">No holdings yet</h2>
          <p className="text-gray-500 text-sm">Add stocks to see dividend data</p>
        </div>
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-9 h-9 rounded-xl bg-[#32D74B]/10 flex items-center justify-center">
                  <PiggyBank size={18} className="text-[#32D74B]" />
                </div>
                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                  Est. Annual Income
                </span>
              </div>
              <p className="text-2xl font-black text-[#32D74B] tabular-nums">${fmt(summary?.total_annual ?? 0)}</p>
            </div>
            <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-9 h-9 rounded-xl bg-[#39C8FF]/10 flex items-center justify-center">
                  <Calendar size={18} className="text-[#39C8FF]" />
                </div>
                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                  Monthly Income
                </span>
              </div>
              <p className="text-2xl font-black text-[#39C8FF] tabular-nums">${fmt(summary?.total_monthly ?? 0)}</p>
            </div>
            <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-9 h-9 rounded-xl bg-[#FCD535]/10 flex items-center justify-center">
                  <Percent size={18} className="text-[#FCD535]" />
                </div>
                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                  Avg Yield
                </span>
              </div>
              <p className="text-2xl font-black text-[#FCD535] tabular-nums">{(summary?.avg_yield ?? 0).toFixed(2)}%</p>
            </div>
          </div>

          {/* Holdings dividend table */}
          <div className="bg-[#0D1117] border border-white/8 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/8 text-gray-500 text-xs uppercase tracking-wider">
                    <th className="text-left px-4 py-3 font-bold">Ticker</th>
                    <th className="text-right px-4 py-3 font-bold">Value</th>
                    <th className="text-right px-4 py-3 font-bold">Yield</th>
                    <th className="text-right px-4 py-3 font-bold hidden sm:table-cell">Ex-Date</th>
                    <th className="text-right px-4 py-3 font-bold">Annual Div</th>
                    <th className="text-right px-4 py-3 font-bold hidden sm:table-cell">Monthly</th>
                  </tr>
                </thead>
                <tbody>
                  {items
                    .sort((a, b) => b.annual_div - a.annual_div)
                    .map((d) => (
                      <tr key={d.ticker} className="border-b border-white/5 hover:bg-white/[0.02]">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-xs font-black text-white">
                              {d.ticker.slice(0, 2)}
                            </div>
                            <span className="font-bold text-white">{d.ticker}</span>
                          </div>
                        </td>
                        <td className="text-right px-4 py-3 font-mono text-gray-400 tabular-nums">
                          ${fmt(d.value)}
                        </td>
                        <td className="text-right px-4 py-3">
                          <span className={`font-mono font-bold tabular-nums ${d.div_yield > 0 ? "text-[#32D74B]" : "text-gray-600"}`}>
                            {d.div_yield > 0 ? `${d.div_yield.toFixed(2)}%` : "\u2014"}
                          </span>
                        </td>
                        <td className="text-right px-4 py-3 text-gray-500 text-xs hidden sm:table-cell">
                          {d.ex_date !== "N/A" ? d.ex_date : "\u2014"}
                        </td>
                        <td className="text-right px-4 py-3">
                          <span className={`font-mono font-bold tabular-nums ${d.annual_div > 0 ? "text-[#32D74B]" : "text-gray-600"}`}>
                            {d.annual_div > 0 ? `$${fmt(d.annual_div)}` : "\u2014"}
                          </span>
                        </td>
                        <td className="text-right px-4 py-3 text-gray-400 font-mono hidden sm:table-cell tabular-nums">
                          {d.monthly_div > 0 ? `$${fmt(d.monthly_div)}` : "\u2014"}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>

            <div className="px-4 py-3 border-t border-white/8 text-xs text-gray-600">
              <TrendingUp size={10} className="inline mr-1" />
              Dividend data from Yahoo Finance. Yields are trailing 12-month. Actual dividends may vary.
            </div>
          </div>
        </>
      )}
    </div>
    </ProGate>
  );
}
