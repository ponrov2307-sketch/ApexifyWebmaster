"use client";

import { useState } from "react";
import { usePortfolio } from "@/lib/hooks";
import { useLang, tr } from "@/lib/i18n";
import { logoUrl, fmt } from "@/lib/dashboard-helpers";
import { Grid3x3, Loader2, ArrowUpDown, TrendingUp, TrendingDown } from "lucide-react";
import ProGate from "@/components/pro-gate";

function heatColor(pnl: number): string {
  if (pnl > 5) return "#00C853";
  if (pnl > 2) return "#32D74B";
  if (pnl > 0) return "#4CAF50";
  if (pnl > -2) return "#E53935";
  if (pnl > -5) return "#FF453A";
  return "#CC0000";
}

type SortKey = "ticker" | "alloc" | "pnl_pct" | "value" | "pnl";

export default function HeatmapPage() {
  const { lang } = useLang();
  const { items: portfolio, summary, loading } = usePortfolio("USD", 30000);
  const [tableSort, setTableSort] = useState<SortKey>("alloc");
  const [tableAsc, setTableAsc] = useState(false);

  const totalValue = summary?.total_value || 0;

  const stocks = portfolio
    .map((s) => ({
      ticker: s.ticker,
      value: s.value,
      price: s.price,
      shares: s.shares,
      avg_cost: s.avg_cost,
      pnl_pct: s.pnl_pct,
      pnl: s.pnl,
      alloc: totalValue > 0 ? (s.value / totalValue) * 100 : 0,
    }))
    .sort((a, b) => b.alloc - a.alloc);

  const toggleSort = (key: SortKey) => {
    if (tableSort === key) setTableAsc(!tableAsc);
    else { setTableSort(key); setTableAsc(key === "ticker"); }
  };

  const tableSorted = [...stocks].sort((a, b) => {
    const dir = tableAsc ? 1 : -1;
    if (tableSort === "ticker") return a.ticker.localeCompare(b.ticker) * dir;
    return ((a[tableSort] || 0) - (b[tableSort] || 0)) * dir;
  });

  return (
    <ProGate>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-black tracking-wide flex items-center gap-3" style={{ color: 'var(--text-primary)' }}>
            <Grid3x3 className="text-[#FF9500]" size={24} />
            {tr("menu.heatmap", lang)}
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            {lang === "TH"
              ? "สัดส่วนพอร์ตและกำไร/ขาดทุนรายตัว"
              : "Portfolio allocation & per-stock P&L"}
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
          </div>
        ) : stocks.length === 0 ? (
          <div className="border rounded-2xl p-12 text-center" style={{ background: 'var(--bg-card)', borderColor: 'var(--border-default)' }}>
            <Grid3x3 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h2 className="text-lg font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
              {lang === "TH" ? "ยังไม่มีหุ้นในพอร์ต" : "No stocks in portfolio"}
            </h2>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              {lang === "TH" ? "เพิ่มหุ้นเพื่อดู Heatmap" : "Add stocks to see the heatmap"}
            </p>
          </div>
        ) : (
          <>
            {/* Treemap — single container with proportional rectangles */}
            <div className="border rounded-2xl overflow-hidden mb-4" style={{ background: 'var(--bg-card)', borderColor: 'var(--border-default)' }}>
              <div className="flex flex-wrap" style={{ minHeight: 400 }}>
                {stocks.map((s) => {
                  const widthPct = Math.max(s.alloc, 8);
                  const up = s.pnl_pct >= 0;
                  const color = heatColor(s.pnl_pct);
                  const bgAlpha = Math.min(0.4, 0.15 + Math.abs(s.pnl_pct) * 0.03);

                  return (
                    <div
                      key={s.ticker}
                      className="relative border border-black/30 flex flex-col items-center justify-center p-3 transition-all hover:brightness-125 cursor-default group"
                      style={{
                        width: `${widthPct}%`,
                        minWidth: 90,
                        minHeight: stocks.length <= 4 ? 200 : 140,
                        flexGrow: s.alloc,
                        background: `rgba(${up ? "50,215,75" : "255,69,58"}, ${bgAlpha})`,
                      }}
                    >
                      <div className="absolute inset-0 opacity-20 pointer-events-none" style={{ background: color }} />
                      <div className="relative z-10 text-center">
                        <img
                          src={logoUrl(s.ticker)}
                          alt=""
                          className="w-8 h-8 rounded-full mx-auto mb-1 border border-white/20"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                        />
                        <p className="text-xl font-black text-white drop-shadow-lg leading-none">{s.ticker}</p>
                        <p className="text-2xl font-black tabular-nums mt-1.5 drop-shadow-lg" style={{ color }}>
                          {up ? "+" : ""}{s.pnl_pct.toFixed(2)}%
                        </p>
                        <p className="text-xs text-white/70 font-bold mt-1 tabular-nums">
                          {s.alloc.toFixed(1)}% {lang === "TH" ? "ของพอร์ต" : "of portfolio"}
                        </p>
                        <p className="text-[10px] text-white/40 font-mono mt-0.5 tabular-nums">
                          ${s.value.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                        </p>
                      </div>
                      <div className="absolute bottom-2 left-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="bg-black/80 backdrop-blur-sm rounded-lg px-2 py-1 text-center">
                          <span className="text-[10px] text-gray-300 tabular-nums">
                            P&L: {up ? "+" : ""}${s.pnl.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Summary bar */}
            <div className="border rounded-2xl p-4 mb-4" style={{ background: 'var(--bg-card)', borderColor: 'var(--border-default)' }}>
              <div className="flex items-center justify-between text-sm">
                <span style={{ color: 'var(--text-muted)' }}>
                  {stocks.length} {lang === "TH" ? "หุ้น" : "stocks"} ·{" "}
                  {lang === "TH" ? "มูลค่ารวม" : "Total"} ${totalValue.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                </span>
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded" style={{ background: "rgba(50,215,75,0.4)" }} />
                    <span style={{ color: 'var(--text-muted)' }}>{lang === "TH" ? "กำไร" : "Profit"}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded" style={{ background: "rgba(255,69,58,0.4)" }} />
                    <span style={{ color: 'var(--text-muted)' }}>{lang === "TH" ? "ขาดทุน" : "Loss"}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* ═══ Data Table ═══ */}
            <div className="border rounded-2xl overflow-hidden" style={{ background: 'var(--bg-card)', borderColor: 'var(--border-default)' }}>
              <div className="px-4 py-3 flex items-center gap-2" style={{ borderBottom: '1px solid var(--border-default)' }}>
                <ArrowUpDown size={14} style={{ color: 'var(--text-muted)' }} />
                <span className="text-xs font-black tracking-widest uppercase" style={{ color: 'var(--text-muted)' }}>
                  {lang === "TH" ? "รายละเอียดหุ้น" : "HOLDINGS DETAIL"}
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      {[
                        { key: "ticker" as SortKey, label: lang === "TH" ? "หุ้น" : "Stock" },
                        { key: "alloc" as SortKey, label: lang === "TH" ? "สัดส่วน" : "Alloc %" },
                        { key: "value" as SortKey, label: lang === "TH" ? "มูลค่า" : "Value" },
                        { key: "pnl_pct" as SortKey, label: "P&L %" },
                        { key: "pnl" as SortKey, label: "P&L $" },
                      ].map(col => (
                        <th
                          key={col.key}
                          className="px-4 py-2.5 text-left text-[10px] font-black tracking-wider uppercase cursor-pointer hover:opacity-80"
                          style={{ color: 'var(--text-dim)' }}
                          onClick={() => toggleSort(col.key)}
                        >
                          {col.label} {tableSort === col.key && (tableAsc ? "↑" : "↓")}
                        </th>
                      ))}
                      <th className="px-4 py-2.5 text-left text-[10px] font-black tracking-wider uppercase" style={{ color: 'var(--text-dim)' }}>
                        {lang === "TH" ? "ราคา" : "Price"}
                      </th>
                      <th className="px-4 py-2.5 text-left text-[10px] font-black tracking-wider uppercase" style={{ color: 'var(--text-dim)' }}>
                        {lang === "TH" ? "จำนวน" : "Shares"}
                      </th>
                      <th className="px-4 py-2.5 text-left text-[10px] font-black tracking-wider uppercase" style={{ color: 'var(--text-dim)' }}>
                        {lang === "TH" ? "ต้นทุน" : "Avg Cost"}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableSorted.map((s) => {
                      const up = s.pnl_pct >= 0;
                      const color = up ? "#32D74B" : "#FF453A";
                      return (
                        <tr key={s.ticker} className="hover:brightness-110 transition-colors" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <img src={logoUrl(s.ticker)} alt="" className="w-6 h-6 rounded-full" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                              <span className="font-black" style={{ color: 'var(--text-primary)' }}>{s.ticker}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--input-bg)' }}>
                                <div className="h-full rounded-full" style={{ width: `${Math.min(100, s.alloc)}%`, background: color }} />
                              </div>
                              <span className="tabular-nums font-bold text-xs" style={{ color: 'var(--text-secondary)' }}>{s.alloc.toFixed(1)}%</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 tabular-nums font-bold" style={{ color: 'var(--text-primary)' }}>${fmt(s.value)}</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1">
                              {up ? <TrendingUp size={12} style={{ color }} /> : <TrendingDown size={12} style={{ color }} />}
                              <span className="tabular-nums font-black" style={{ color }}>{up ? "+" : ""}{s.pnl_pct.toFixed(2)}%</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 tabular-nums font-bold" style={{ color }}>{up ? "+" : ""}${fmt(Math.abs(s.pnl))}</td>
                          <td className="px-4 py-3 tabular-nums" style={{ color: 'var(--text-secondary)' }}>${fmt(s.price)}</td>
                          <td className="px-4 py-3 tabular-nums" style={{ color: 'var(--text-muted)' }}>{s.shares}</td>
                          <td className="px-4 py-3 tabular-nums" style={{ color: 'var(--text-muted)' }}>${fmt(s.avg_cost)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </ProGate>
  );
}
