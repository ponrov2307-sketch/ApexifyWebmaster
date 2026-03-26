"use client";

import { useState, useEffect, useRef } from "react";
import { usePortfolio } from "@/lib/hooks";
import { useLang, tr } from "@/lib/i18n";
import { logoUrl, fmt } from "@/lib/dashboard-helpers";
import api from "@/lib/api";
import { Grid3x3, Loader2, ArrowUpDown, TrendingUp, TrendingDown } from "lucide-react";
import ProGate from "@/components/pro-gate";

// ── Color helpers ──
function heatColor(v: number): string {
  if (v > 5)  return "#00C853";
  if (v > 2)  return "#32D74B";
  if (v > 0)  return "#4CAF50";
  if (v > -2) return "#E53935";
  if (v > -5) return "#FF453A";
  return "#CC0000";
}
function heatBg(v: number): string {
  const c = v >= 0 ? "50,215,75" : "255,69,58";
  const a = Math.min(0.55, 0.12 + Math.abs(v) * 0.07);
  return `rgba(${c},${a})`;
}

// ── Squarified Treemap (Bruls-Huizing-van Wijk) ──
interface TItem { id: string; weight: number; [k: string]: unknown; }
interface TRect extends TItem { x: number; y: number; w: number; h: number; }

function worstRatio(row: number[], side: number): number {
  const s = row.reduce((a, b) => a + b, 0);
  if (s === 0 || side === 0) return Infinity;
  const s2 = s * s;
  const w2 = side * side;
  let worst = 0;
  for (const r of row) {
    if (r === 0) continue;
    const ratio = Math.max((w2 * r) / s2, s2 / (w2 * r));
    if (ratio > worst) worst = ratio;
  }
  return worst;
}

function treemap(items: TItem[], width: number, height: number): TRect[] {
  if (!items.length) return [];
  const sorted = [...items].sort((a, b) => b.weight - a.weight);
  const total = sorted.reduce((s, i) => s + i.weight, 0);
  if (!total) return [];

  // Normalize areas so they sum to total pixel area
  const area = width * height;
  const areas = sorted.map((it) => (it.weight / total) * area);

  const rects: TRect[] = [];

  function squarify(dataIdx: number[], x: number, y: number, w: number, h: number) {
    if (!dataIdx.length) return;
    if (dataIdx.length === 1) {
      rects.push({ ...sorted[dataIdx[0]], x, y, w, h });
      return;
    }

    const side = Math.min(w, h);
    const isHoriz = w >= h; // lay row along short side
    let row: number[] = [];
    let rowAreas: number[] = [];
    let rest = [...dataIdx];

    // Greedily add items to current row while aspect ratio improves
    row.push(rest.shift()!);
    rowAreas.push(areas[row[0]]);

    while (rest.length > 0) {
      const candidate = rest[0];
      const newRowAreas = [...rowAreas, areas[candidate]];
      if (worstRatio(newRowAreas, side) <= worstRatio(rowAreas, side)) {
        row.push(rest.shift()!);
        rowAreas = newRowAreas;
      } else {
        break;
      }
    }

    // Layout this row
    const rowTotal = rowAreas.reduce((a, b) => a + b, 0);
    const rowThickness = side > 0 ? rowTotal / side : 0;

    let cx = x, cy = y;
    for (let i = 0; i < row.length; i++) {
      const itemLen = rowThickness > 0 ? rowAreas[i] / rowThickness : 0;
      if (isHoriz) {
        // row fills left side vertically
        rects.push({ ...sorted[row[i]], x: cx, y: cy, w: rowThickness, h: itemLen });
        cy += itemLen;
      } else {
        // row fills top side horizontally
        rects.push({ ...sorted[row[i]], x: cx, y: cy, w: itemLen, h: rowThickness });
        cx += itemLen;
      }
    }

    // Recurse on remaining space
    if (rest.length > 0) {
      if (isHoriz) {
        squarify(rest, x + rowThickness, y, w - rowThickness, h);
      } else {
        squarify(rest, x, y + rowThickness, w, h - rowThickness);
      }
    }
  }

  squarify(sorted.map((_, i) => i), 0, 0, width, height);
  return rects;
}

// ── Types ──
type SortKey = "ticker" | "alloc" | "pnl_pct" | "value" | "pnl";
interface Sp500Stock { ticker: string; price: number; change_pct: number; mcap: number; }
type Sp500Data = Record<string, Sp500Stock[]>;

export default function HeatmapPage() {
  const { lang } = useLang();
  const { items: portfolio, summary, loading } = usePortfolio("USD", 30000);
  const [tableSort, setTableSort] = useState<SortKey>("alloc");
  const [tableAsc, setTableAsc] = useState(false);
  const [tab, setTab] = useState<"portfolio" | "sp500">("portfolio");
  const [sp500, setSp500] = useState<Sp500Data | null>(null);
  const [sp500Loading, setSp500Loading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 900, h: 480 });

  // measure container
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => {
      setDims({ w: e.contentRect.width, h: Math.max(500, Math.min(800, e.contentRect.width * 0.55)) });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (tab !== "sp500" || sp500) return;
    setSp500Loading(true);
    api.get<Sp500Data>("/api/market/sp500-heatmap")
      .then(({ data }) => setSp500(data))
      .catch(() => {})
      .finally(() => setSp500Loading(false));
  }, [tab, sp500]);

  const totalValue = summary?.total_value || 0;
  const stocks = portfolio
    .map((s) => ({
      id: s.ticker, ticker: s.ticker, weight: s.value,
      value: s.value, price: s.price, shares: s.shares,
      avg_cost: s.avg_cost, pnl_pct: s.pnl_pct, pnl: s.pnl,
      alloc: totalValue > 0 ? (s.value / totalValue) * 100 : 0,
    }))
    .filter((s) => s.weight > 0);

  const toggleSort = (key: SortKey) => {
    if (tableSort === key) setTableAsc(!tableAsc);
    else { setTableSort(key); setTableAsc(key === "ticker"); }
  };
  const tableSorted = [...stocks].sort((a, b) => {
    const dir = tableAsc ? 1 : -1;
    if (tableSort === "ticker") return a.ticker.localeCompare(b.ticker) * dir;
    return ((a[tableSort as keyof typeof a] as number || 0) - (b[tableSort as keyof typeof b] as number || 0)) * dir;
  });

  // Portfolio treemap nodes
  const portfolioRects = treemap(stocks, dims.w, dims.h);

  // S&P 500 treemap — sectors as big blocks, stocks inside (sized by market cap)
  const sp500Sectors = sp500
    ? Object.entries(sp500).map(([name, stocks]) => ({
        id: name,
        name,
        stocks,
        weight: stocks.reduce((s, x) => s + (x.mcap || 1), 0),
        avg: stocks.length ? stocks.reduce((s, x) => s + x.change_pct, 0) / stocks.length : 0,
      }))
    : [];
  const sectorRects = treemap(sp500Sectors, dims.w, dims.h);

  return (
    <ProGate>
      <div className="w-full">
        {/* Header */}
        <div className="mb-5">
          <h1 className="text-2xl font-black tracking-wide flex items-center gap-3" style={{ color: "var(--text-primary)" }}>
            <Grid3x3 className="text-[#FF9500]" size={24} />
            {tr("menu.heatmap", lang)}
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            {lang === "TH" ? "สัดส่วนพอร์ตและกำไร/ขาดทุนรายตัว" : "Portfolio allocation & per-stock P&L"}
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex gap-2 mb-5">
          {(["portfolio", "sp500"] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                tab === t
                  ? "bg-[#D0FD3E]/10 border border-[#D0FD3E]/30 text-[#D0FD3E]"
                  : "border border-transparent text-gray-500 hover:text-white hover:bg-white/5"
              }`}
            >
              {t === "portfolio" ? (lang === "TH" ? "พอร์ตของฉัน" : "My Portfolio") : "S&P 500"}
            </button>
          ))}
        </div>

        {/* ══ PORTFOLIO TAB ══ */}
        {tab === "portfolio" && (
          loading ? (
            <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" /></div>
          ) : stocks.length === 0 ? (
            <div className="border rounded-2xl p-12 text-center" style={{ background: "var(--bg-card)", borderColor: "var(--border-default)" }}>
              <Grid3x3 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{lang === "TH" ? "ยังไม่มีหุ้นในพอร์ต" : "No stocks in portfolio"}</p>
            </div>
          ) : (
            <>
              {/* Treemap */}
              <div ref={containerRef} className="border rounded-2xl overflow-hidden mb-4 relative" style={{ background: "#0a0e17", borderColor: "var(--border-default)", height: dims.h }}>
                {portfolioRects.map((r) => {
                  const s = r as typeof stocks[0] & TRect;
                  const up = s.pnl_pct >= 0;
                  const color = heatColor(s.pnl_pct);
                  const showLogo = r.w > 70 && r.h > 70;
                  const showLabel = r.w > 45 && r.h > 35;
                  return (
                    <div key={s.ticker}
                      className="absolute group transition-all hover:z-10 hover:brightness-125 overflow-hidden"
                      style={{ left: r.x, top: r.y, width: r.w, height: r.h, border: "1px solid rgba(0,0,0,0.6)", background: heatBg(s.pnl_pct) }}
                    >
                      <div className="absolute inset-0 opacity-15" style={{ background: color }} />
                      {showLabel && (
                        <div className="relative z-10 flex flex-col items-center justify-center h-full text-center px-1">
                          {showLogo && (
                            <img src={logoUrl(s.ticker)} alt="" className="w-7 h-7 rounded-full mb-1 border border-white/20"
                              onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
                          )}
                          <p className="font-black text-white leading-none" style={{ fontSize: Math.max(9, Math.min(16, r.w / 5)) }}>{s.ticker}</p>
                          <p className="font-black tabular-nums" style={{ color, fontSize: Math.max(8, Math.min(18, r.w / 4.5)) }}>
                            {up ? "+" : ""}{s.pnl_pct.toFixed(2)}%
                          </p>
                          {r.h > 80 && <p className="text-white/50 tabular-nums" style={{ fontSize: 9 }}>{s.alloc.toFixed(1)}%</p>}
                        </div>
                      )}
                      {/* hover tooltip */}
                      <div className="absolute bottom-1 left-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity z-20">
                        <div className="bg-black/90 rounded px-1.5 py-1 text-center">
                          <p className="text-[10px] text-white font-bold">{s.ticker}</p>
                          <p className="text-[9px] tabular-nums" style={{ color }}>P&L: {up ? "+" : ""}${s.pnl.toFixed(2)} ({up ? "+" : ""}{s.pnl_pct.toFixed(2)}%)</p>
                          <p className="text-[9px] text-gray-400 tabular-nums">${fmt(s.value)} · {s.alloc.toFixed(1)}%</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Summary */}
              <div className="border rounded-2xl p-4 mb-4 flex items-center justify-between text-sm" style={{ background: "var(--bg-card)", borderColor: "var(--border-default)" }}>
                <span style={{ color: "var(--text-muted)" }}>
                  {stocks.length} {lang === "TH" ? "หุ้น" : "stocks"} · {lang === "TH" ? "มูลค่ารวม" : "Total"} ${totalValue.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                </span>
                <div className="flex items-center gap-4 text-xs">
                  {[["rgba(50,215,75,0.5)", lang === "TH" ? "กำไร" : "Profit"], ["rgba(255,69,58,0.5)", lang === "TH" ? "ขาดทุน" : "Loss"]].map(([bg, label]) => (
                    <div key={label} className="flex items-center gap-1.5">
                      <div className="w-3 h-3 rounded" style={{ background: bg as string }} />
                      <span style={{ color: "var(--text-muted)" }}>{label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Table */}
              <div className="border rounded-2xl overflow-hidden" style={{ background: "var(--bg-card)", borderColor: "var(--border-default)" }}>
                <div className="px-4 py-3 flex items-center gap-2" style={{ borderBottom: "1px solid var(--border-default)" }}>
                  <ArrowUpDown size={14} style={{ color: "var(--text-muted)" }} />
                  <span className="text-xs font-black tracking-widest uppercase" style={{ color: "var(--text-muted)" }}>{lang === "TH" ? "รายละเอียดหุ้น" : "HOLDINGS DETAIL"}</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                        {([["ticker","Stock/หุ้น"],["alloc","Alloc %"],["value","Value/มูลค่า"],["pnl_pct","P&L %"],["pnl","P&L $"]] as [SortKey,string][]).map(([key, label]) => (
                          <th key={key} className="px-4 py-2.5 text-left text-[10px] font-black tracking-wider uppercase cursor-pointer hover:opacity-80" style={{ color: "var(--text-dim)" }} onClick={() => toggleSort(key)}>
                            {label} {tableSort === key && (tableAsc ? "↑" : "↓")}
                          </th>
                        ))}
                        {["Price/ราคา","Shares/จำนวน","Avg Cost/ต้นทุน"].map((h) => (
                          <th key={h} className="px-4 py-2.5 text-left text-[10px] font-black tracking-wider uppercase" style={{ color: "var(--text-dim)" }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {tableSorted.map((s) => {
                        const up = s.pnl_pct >= 0;
                        const color = up ? "#32D74B" : "#FF453A";
                        return (
                          <tr key={s.ticker} className="hover:brightness-110 transition-colors" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <img src={logoUrl(s.ticker)} alt="" className="w-6 h-6 rounded-full" onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
                                <span className="font-black" style={{ color: "var(--text-primary)" }}>{s.ticker}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: "var(--input-bg)" }}>
                                  <div className="h-full rounded-full" style={{ width: `${Math.min(100, s.alloc)}%`, background: color }} />
                                </div>
                                <span className="tabular-nums font-bold text-xs" style={{ color: "var(--text-secondary)" }}>{s.alloc.toFixed(1)}%</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 tabular-nums font-bold" style={{ color: "var(--text-primary)" }}>${fmt(s.value)}</td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-1">
                                {up ? <TrendingUp size={12} style={{ color }} /> : <TrendingDown size={12} style={{ color }} />}
                                <span className="tabular-nums font-black" style={{ color }}>{up ? "+" : ""}{s.pnl_pct.toFixed(2)}%</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 tabular-nums font-bold" style={{ color }}>{up ? "+" : ""}${fmt(Math.abs(s.pnl))}</td>
                            <td className="px-4 py-3 tabular-nums" style={{ color: "var(--text-secondary)" }}>${fmt(s.price)}</td>
                            <td className="px-4 py-3 tabular-nums" style={{ color: "var(--text-muted)" }}>{s.shares}</td>
                            <td className="px-4 py-3 tabular-nums" style={{ color: "var(--text-muted)" }}>${fmt(s.avg_cost)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )
        )}

        {/* ══ S&P 500 TAB ══ */}
        {tab === "sp500" && (
          sp500Loading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
              <p className="text-sm text-gray-500">Loading S&P 500 data...</p>
            </div>
          ) : !sp500 ? (
            <div className="border rounded-2xl p-12 text-center" style={{ background: "var(--bg-card)", borderColor: "var(--border-default)" }}>
              <p className="text-gray-500">Failed to load S&P 500 data</p>
            </div>
          ) : (
            <>
              {/* Legend */}
              <div className="flex flex-wrap items-center gap-3 text-[10px] mb-3 px-1">
                <span className="text-gray-500 font-bold">% today:</span>
                {([["#CC0000","< -5%"],["#FF453A","-2~5%"],["#E53935","0~2%"],["#4CAF50","0~2%"],["#32D74B","2~5%"],["#00C853","> 5%"]] as [string,string][]).map(([c,l]) => (
                  <div key={l} className="flex items-center gap-1">
                    <div className="w-2.5 h-2.5 rounded-sm" style={{ background: c }} />
                    <span className="text-gray-500">{l}</span>
                  </div>
                ))}
              </div>

              {/* Big treemap — sectors as rectangles, stocks inside */}
              <div className="border rounded-2xl overflow-hidden mb-3" style={{ background: "#0a0e17", borderColor: "var(--border-default)", height: dims.h, position: "relative" }}>
                {sectorRects.map((sr) => {
                  const sector = sr as typeof sp500Sectors[0] & TRect;
                  const avgUp = sector.avg >= 0;
                  const avgColor = heatColor(sector.avg);
                  // layout stocks inside this sector rect
                  const stockItems = sector.stocks.map((s) => ({ ...s, id: s.ticker, weight: s.mcap || 1 }));
                  const stockRects = treemap(stockItems, sr.w - 2, sr.h - 22);
                  return (
                    <div key={sector.name} className="absolute overflow-hidden" style={{ left: sr.x, top: sr.y, width: sr.w, height: sr.h, border: "3px solid #0a0e17" }}>
                      {/* Sector header */}
                      <div className="flex items-center justify-between px-1.5 absolute top-0 left-0 right-0 z-10" style={{ height: 20, background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)" }}>
                        <span className="text-[9px] font-black text-white tracking-wider truncate">{sector.name}</span>
                        <span className="text-[9px] font-black tabular-nums shrink-0 ml-1" style={{ color: avgColor }}>
                          {avgUp ? "+" : ""}{sector.avg.toFixed(2)}%
                        </span>
                      </div>
                      {/* Stocks */}
                      <div className="absolute" style={{ top: 20, left: 0, right: 0, bottom: 0 }}>
                        {stockRects.map((stockR) => {
                          const s = stockR as Sp500Stock & TRect;
                          const up = s.change_pct >= 0;
                          const color = heatColor(s.change_pct);
                          const showTicker = stockR.w > 28 && stockR.h > 20;
                          const showPct = stockR.w > 35 && stockR.h > 32;
                          return (
                            <div key={s.ticker}
                              className="absolute group overflow-hidden hover:z-20 hover:brightness-125 transition-all"
                              style={{ left: stockR.x, top: stockR.y, width: stockR.w, height: stockR.h, border: "1px solid rgba(0,0,0,0.5)", background: heatBg(s.change_pct) }}
                            >
                              <div className="absolute inset-0 opacity-10" style={{ background: color }} />
                              {showTicker && (
                                <div className="relative z-10 flex flex-col items-center justify-center h-full text-center">
                                  <p className="font-black text-white leading-none" style={{ fontSize: Math.max(7, Math.min(11, stockR.w / 4.5)) }}>{s.ticker}</p>
                                  {showPct && (
                                    <p className="font-black tabular-nums" style={{ color, fontSize: Math.max(7, Math.min(10, stockR.w / 5)) }}>
                                      {up ? "+" : ""}{s.change_pct.toFixed(2)}%
                                    </p>
                                  )}
                                </div>
                              )}
                              {/* Tooltip */}
                              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-0.5 opacity-0 group-hover:opacity-100 transition-opacity z-30 pointer-events-none">
                                <div className="bg-black/95 border border-white/10 rounded-lg px-2 py-1 text-[10px] whitespace-nowrap shadow-xl">
                                  <p className="text-white font-black">{s.ticker}</p>
                                  <p className="tabular-nums" style={{ color }}>{up ? "+" : ""}{s.change_pct.toFixed(2)}%</p>
                                  <p className="text-gray-400">${s.price.toFixed(2)}</p>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
              <p className="text-[10px] text-gray-600 text-center">
                {Object.values(sp500).flat().length} stocks · {Object.keys(sp500).length} sectors · cached 5 min
              </p>
            </>
          )
        )}
      </div>
    </ProGate>
  );
}
