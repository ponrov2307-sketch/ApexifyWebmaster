"use client";

import { useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";
import { usePortfolio } from "@/lib/hooks";
import {
  X,
  TrendingUp,
  TrendingDown,
  Zap,
  Sparkles,
} from "lucide-react";

function fmt(n: number) {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function DailySummaryPopup() {
  const { lang } = useLang();
  const { items, summary, loading } = usePortfolio("USD", 0);
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (loading || !summary || items.length === 0) return;

    const today = new Date().toDateString();
    const lastShown = localStorage.getItem("daily_summary_shown");
    if (lastShown === today) return;

    const timer = setTimeout(() => {
      setShow(true);
      localStorage.setItem("daily_summary_shown", today);
    }, 2000);

    return () => clearTimeout(timer);
  }, [loading, summary, items]);

  if (!show || !summary || items.length === 0) return null;

  const up = summary.total_pnl >= 0;
  const profitColor = up ? "#32D74B" : "#FF453A";
  const pnlPct = summary.total_cost > 0 ? (summary.total_pnl / summary.total_cost) * 100 : 0;
  const totalValue = summary.total_value;

  // Sort by P&L % descending
  const sorted = [...items].sort((a, b) => b.pnl_pct - a.pnl_pct);

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={() => setShow(false)}>
      <div
        className="w-[92vw] max-w-md max-h-[85vh] bg-gradient-to-b from-[#161B22] to-[#0D1117] border border-white/10 rounded-3xl overflow-hidden shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top glow */}
        <div className="h-[2px] shrink-0" style={{ background: `linear-gradient(90deg, transparent, ${profitColor}60, transparent)` }} />

        <div className="p-6 overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles size={18} className="text-[#D0FD3E]" />
              <h2 className="text-lg font-black text-white">
                {lang === "TH" ? "สรุปพอร์ตวันนี้" : "Daily Portfolio Summary"}
              </h2>
            </div>
            <button onClick={() => setShow(false)} className="text-gray-500 hover:text-white p-1">
              <X size={18} />
            </button>
          </div>

          {/* Portfolio value */}
          <div className="text-center mb-4">
            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">
              {lang === "TH" ? "มูลค่าพอร์ตรวม" : "Total Portfolio Value"}
            </p>
            <p className="text-3xl font-black text-white tabular-nums">${fmt(summary.total_value)}</p>
            <p className="text-base font-black tabular-nums mt-1" style={{ color: profitColor }}>
              {up ? "+" : "-"}${fmt(Math.abs(summary.total_pnl))} ({up ? "+" : ""}{pnlPct.toFixed(2)}%)
            </p>
          </div>

          {/* Per-stock P&L breakdown */}
          <div className="mb-4">
            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-2 px-1">
              {lang === "TH" ? "กำไร/ขาดทุนรายตัว" : "Per-Stock P&L"}
            </p>
            <div className="space-y-1.5">
              {sorted.map((s) => {
                const sUp = s.pnl_pct >= 0;
                const alloc = totalValue > 0 ? (s.value / totalValue) * 100 : 0;
                return (
                  <div
                    key={s.ticker}
                    className="flex items-center justify-between bg-white/[0.03] border border-white/5 rounded-lg px-3 py-2"
                  >
                    <div className="flex items-center gap-2">
                      {sUp ? (
                        <TrendingUp size={12} className="text-[#32D74B]" />
                      ) : (
                        <TrendingDown size={12} className="text-[#FF453A]" />
                      )}
                      <span className="text-sm font-black text-white">{s.ticker}</span>
                      <span className="text-[10px] text-gray-600">{alloc.toFixed(1)}%</span>
                    </div>
                    <div className="text-right">
                      <span
                        className="text-sm font-bold tabular-nums"
                        style={{ color: sUp ? "#32D74B" : "#FF453A" }}
                      >
                        {sUp ? "+" : ""}{s.pnl_pct.toFixed(2)}%
                      </span>
                      <span className="text-[10px] text-gray-500 ml-1.5 tabular-nums">
                        {sUp ? "+" : ""}${fmt(s.pnl)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* THB value */}
          {summary.thb_rate > 0 && (
            <div className="bg-white/[0.03] border border-white/5 rounded-lg px-3 py-2 mb-4 flex items-center justify-between">
              <span className="text-xs text-gray-500 font-bold">
                {lang === "TH" ? "มูลค่าเป็นบาท" : "THB Value"}
              </span>
              <span className="text-sm font-black text-[#FCD535] tabular-nums">
                ฿{(summary.total_value * summary.thb_rate).toLocaleString("en-US", { maximumFractionDigits: 0 })}
              </span>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
            <span>{items.length} {lang === "TH" ? "หุ้น" : "stocks"}</span>
            <span className="flex items-center gap-1">
              <Zap size={10} className="text-[#D0FD3E]" />
              <span className="text-[10px] text-[#D0FD3E]">LIVE</span>
            </span>
          </div>

          <button
            onClick={() => setShow(false)}
            className="w-full py-3 bg-[#D0FD3E] text-black font-black rounded-xl text-sm hover:bg-[#c5f232] transition-colors"
          >
            {lang === "TH" ? "เข้าสู่แดชบอร์ด" : "Go to Dashboard"}
          </button>
        </div>
      </div>
    </div>
  );
}
