"use client";

import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { PortfolioItem, PortfolioSummary } from "@/lib/hooks";
import { fmt } from "@/lib/dashboard-helpers";

interface Props {
  items: PortfolioItem[];
  summary: PortfolioSummary;
  currSymbol: string;
}

export default function PerformanceAttribution({ items, summary, currSymbol }: Props) {
  return (
    <div className="rounded-[22px] border border-white/5 p-5 md:p-6 space-y-4"
      style={{ background: "linear-gradient(180deg, rgba(14,25,35,0.9), rgba(9,16,24,0.92))" }}
    >
      <p className="text-xs font-black text-[#D0FD3E] tracking-widest uppercase">Performance Attribution</p>
      <div className="space-y-3">
        {[...items].sort((a, b) => Math.abs(b.pnl) - Math.abs(a.pnl)).map((s) => {
          const contribution = summary.total_cost > 0 ? (s.pnl / summary.total_cost) * 100 : 0;
          const up = s.pnl >= 0;
          return (
            <div key={s.ticker} className="flex items-center gap-3">
              <span className="text-sm text-gray-400 w-20 truncate font-bold">{s.ticker}</span>
              <div className="flex-1 h-6 bg-white/5 rounded-lg overflow-hidden relative">
                <div className="h-full rounded-lg transition-all duration-500"
                  style={{
                    width: `${Math.min(Math.abs(contribution) * 10, 100)}%`,
                    background: up ? "rgba(50,215,75,0.3)" : "rgba(255,69,58,0.3)",
                  }} />
              </div>
              <div className="flex items-center gap-1 w-28 justify-end">
                {up ? <ArrowUpRight size={12} className="text-[#32D74B]" /> : <ArrowDownRight size={12} className="text-[#FF453A]" />}
                <span className="text-sm font-mono font-bold tabular-nums"
                  style={{ color: up ? "#32D74B" : "#FF453A" }}>
                  {up ? "+" : ""}{currSymbol}{fmt(s.pnl)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
