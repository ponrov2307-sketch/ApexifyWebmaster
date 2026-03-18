"use client";

import { CandlestickChart, Crown } from "lucide-react";
import { PortfolioItem } from "@/lib/hooks";
import { Lang, tr } from "@/lib/i18n";
import { buildTradePlan, ACTION_THEME, fmt, fmtPct } from "@/lib/dashboard-helpers";

interface Props {
  items: PortfolioItem[];
  isProPlan: boolean;
  currSymbol: string;
  lang: Lang;
  onChart: (ticker: string) => void;
}

export default function TradePlanPanel({ items, isProPlan, currSymbol, lang, onChart }: Props) {
  if (items.length === 0) return null;
  const display = isProPlan ? items : items.slice(0, 3);

  return (
    <div className="rounded-[22px] border border-white/8 p-5 md:p-6 space-y-4"
      style={{ background: "linear-gradient(180deg, rgba(14,25,35,0.9), rgba(9,16,24,0.92))", backdropFilter: "blur(14px)", boxShadow: "0 14px 34px rgba(0,0,0,0.42), inset 0 1px 0 rgba(255,255,255,0.06)" }}
    >
      <div className="flex justify-between items-center flex-wrap gap-3">
        <div>
          <p className="text-xs md:text-sm font-black text-[#20D6A1] tracking-widest uppercase">{tr("trade_plan.title", lang)}</p>
          <p className="text-[10px] text-gray-500 font-bold tracking-wide">{tr("trade_plan.subtitle", lang)}</p>
        </div>
        <span className={`text-[10px] font-black tracking-widest px-3 py-1 rounded-full border ${isProPlan ? "text-[#32D74B] border-[#32D74B]/30 bg-[#32D74B]/10" : "text-[#FCD535] border-[#FCD535]/30 bg-[#FCD535]/10"}`}>
          {isProPlan ? "UNLOCKED" : "PRO FEATURE"}
        </span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {display.map((s) => {
          const plan = buildTradePlan(s);
          const theme = ACTION_THEME[plan.action] || { text: "text-gray-300", bg: "bg-white/5 border-white/10" };

          return (
            <div key={s.ticker} className="bg-[#0B0E14]/70 border border-white/5 rounded-2xl p-4 space-y-3 shadow-inner">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-xl font-black text-white tracking-wider">{plan.ticker}</p>
                  <p className="text-[11px] text-gray-500 font-bold">
                    Current {currSymbol}{fmt(s.price)} · Avg {currSymbol}{fmt(s.avg_cost)}
                  </p>
                </div>
                <div className="text-right space-y-1">
                  <span className={`text-[10px] font-black tracking-widest px-3 py-1 rounded-full border ${theme.text} ${theme.bg}`}>
                    {plan.action}
                  </span>
                  <p className="text-[9px] text-gray-400 font-black">
                    {plan.signal} · C{plan.confidence}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <span className={`text-sm font-black ${plan.pnl_pct >= 0 ? "text-[#32D74B]" : "text-[#FF453A]"}`}>
                  Profit {fmtPct(plan.pnl_pct)}
                </span>
                <span className="text-xs text-[#39C8FF] font-bold">Entry {currSymbol}{fmt(plan.entryLow)}-{currSymbol}{fmt(plan.entryHigh)}</span>
                <span className="text-xs text-[#32D74B] font-bold">TP1 {currSymbol}{fmt(plan.tp1)}</span>
                <span className="text-xs text-[#20D6A1] font-bold">TP2 {currSymbol}{fmt(plan.tp2)}</span>
                <span className="text-xs text-[#FF453A] font-bold">SL {currSymbol}{fmt(plan.sl)}</span>
                <span className="text-xs text-[#FCD535] font-black">R:R {plan.rr.toFixed(2)}</span>
              </div>

              <p className="text-xs text-gray-400 leading-relaxed">{plan.reason}</p>

              <div className="flex gap-2">
                <button onClick={() => onChart(s.ticker)}
                  className="flex-1 flex items-center justify-center gap-1 bg-[#D0FD3E] text-black font-black rounded-lg text-xs py-2">
                  <CandlestickChart size={12} /> Chart
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {!isProPlan && items.length > 3 && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <span className="text-xs text-gray-500">{items.length - 3} more hidden</span>
          <button onClick={() => window.open("/payment", "_self")}
            className="flex items-center gap-1.5 px-5 py-2 bg-[#FCD535] text-black font-black rounded-full text-xs hover:scale-105 transition-transform shadow-[0_0_15px_rgba(252,213,53,0.3)]">
            <Crown size={12} /> UNLOCK
          </button>
        </div>
      )}
    </div>
  );
}
