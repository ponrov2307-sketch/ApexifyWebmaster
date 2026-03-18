"use client";

import { Brain, RefreshCw, X } from "lucide-react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Lang } from "@/lib/i18n";
import StockLogo from "@/components/stock-logo";
import { fmt, fmtPct } from "@/lib/dashboard-helpers";

interface PortfolioItem {
  ticker: string;
  shares: number;
  avg_cost: number;
  price: number;
  value: number;
  pnl_pct: number;
}

interface Props {
  open: boolean;
  loading: boolean;
  result: string | null;
  lang: Lang;
  items?: PortfolioItem[];
  onClose: () => void;
  onReanalyze: () => void;
}

export default function RebalanceModal({ open, loading, result, lang, items = [], onClose, onReanalyze }: Props) {
  if (!open) return null;

  const total = items.reduce((s, i) => s + Math.max(i.value, 0), 0);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="w-[96vw] max-w-[900px] max-h-[90vh] bg-gradient-to-b from-[#111822] to-[#0D1117] border border-purple-500/30 rounded-3xl overflow-hidden shadow-[0_0_60px_rgba(168,85,247,0.15)] flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="relative px-6 py-5 border-b border-white/8">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-purple-500/50 to-transparent" />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/25 flex items-center justify-center">
                <Brain size={20} className="text-purple-400" />
              </div>
              <div>
                <h2 className="text-lg font-black text-white tracking-wide">AI Rebalance Strategy</h2>
                <p className="text-[11px] text-purple-400/70 font-bold">Powered by Gemini AI</p>
              </div>
            </div>
            <button onClick={onClose} className="text-gray-500 hover:text-white p-2 hover:bg-white/5 rounded-lg transition-colors"><X size={20} /></button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <div className="relative">
                <div className="w-16 h-16 rounded-full border-2 border-purple-500/20 border-t-purple-500 animate-spin" />
                <Brain size={24} className="text-purple-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
              </div>
              <span className="text-gray-400 text-sm font-bold">{lang === "TH" ? "AI กำลังวิเคราะห์พอร์ตของคุณ..." : "AI is analyzing your portfolio..."}</span>
              <span className="text-gray-600 text-xs">{lang === "TH" ? "อาจใช้เวลา 10-20 วินาที" : "This may take 10-20 seconds"}</span>
            </div>
          ) : (
            <>
              {/* AI Result */}
              {result && (
                <div className="max-w-none mb-6">
                  <Markdown remarkPlugins={[remarkGfm]} components={{
                    h2: ({ children }) => (
                      <h2 className="text-lg font-black text-white mt-6 mb-3 tracking-wide flex items-center gap-2 border-b border-purple-500/20 pb-2">
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => <h3 className="text-base font-bold text-gray-200 mt-4 mb-2">{children}</h3>,
                    p: ({ children }) => <p className="text-gray-300 leading-relaxed text-sm my-2">{children}</p>,
                    ul: ({ children }) => <ul className="space-y-1.5 my-2">{children}</ul>,
                    li: ({ children }) => <li className="text-gray-300 text-sm flex items-start gap-1.5"><span className="text-purple-400 mt-0.5">▸</span><span>{children}</span></li>,
                    strong: ({ children }) => <strong className="text-[#D0FD3E] font-black">{children}</strong>,
                    table: ({ children }) => (
                      <div className="overflow-x-auto mt-3 mb-4 rounded-2xl border border-purple-500/20 shadow-[0_0_20px_rgba(168,85,247,0.05)]">
                        <table className="w-full border-collapse" style={{ background: "rgba(13,17,23,0.6)" }}>{children}</table>
                      </div>
                    ),
                    thead: ({ children }) => <thead className="bg-gradient-to-r from-purple-500/15 to-purple-500/5">{children}</thead>,
                    th: ({ children }) => <th className="px-4 py-3.5 text-[11px] font-black text-purple-300 tracking-wider text-left border-b border-purple-500/30 whitespace-nowrap">{children}</th>,
                    td: ({ children }) => <td className="px-4 py-3.5 text-sm text-gray-200 border-b border-white/5">{children}</td>,
                    tr: ({ children }) => <tr className="hover:bg-purple-500/[0.04] transition-colors">{children}</tr>,
                  }}>{result}</Markdown>
                </div>
              )}

              {/* Portfolio Data Table */}
              {items.length > 0 && (
                <div>
                  <h3 className="text-sm font-black text-gray-400 tracking-wider uppercase mb-3 flex items-center gap-2">
                    <span className="w-8 h-px bg-purple-500/30" />
                    {lang === "TH" ? "ข้อมูลพอร์ตปัจจุบัน" : "Current Portfolio Data"}
                    <span className="flex-1 h-px bg-purple-500/30" />
                  </h3>

                  <div className="overflow-x-auto rounded-xl border border-white/8">
                    <table className="w-full border-collapse" style={{ background: "rgba(13,17,23,0.3)" }}>
                      <thead>
                        <tr className="bg-white/3">
                          <th className="px-4 py-3 text-[10px] font-black text-gray-400 tracking-wider text-left uppercase">{lang === "TH" ? "สินทรัพย์" : "Asset"}</th>
                          <th className="px-4 py-3 text-[10px] font-black text-gray-400 tracking-wider text-right uppercase">{lang === "TH" ? "จำนวน" : "Shares"}</th>
                          <th className="px-4 py-3 text-[10px] font-black text-gray-400 tracking-wider text-right uppercase">{lang === "TH" ? "ต้นทุน" : "Avg Cost"}</th>
                          <th className="px-4 py-3 text-[10px] font-black text-gray-400 tracking-wider text-right uppercase">{lang === "TH" ? "ราคาปัจจุบัน" : "Price"}</th>
                          <th className="px-4 py-3 text-[10px] font-black text-gray-400 tracking-wider text-right uppercase">{lang === "TH" ? "มูลค่า" : "Value"}</th>
                          <th className="px-4 py-3 text-[10px] font-black text-gray-400 tracking-wider text-right uppercase">{lang === "TH" ? "สัดส่วน" : "Alloc %"}</th>
                          <th className="px-4 py-3 text-[10px] font-black text-gray-400 tracking-wider text-right uppercase">P&L</th>
                        </tr>
                      </thead>
                      <tbody>
                        {items
                          .slice()
                          .sort((a, b) => b.value - a.value)
                          .map((item) => {
                            const alloc = total > 0 ? (item.value / total) * 100 : 0;
                            const pnlVal = item.value - item.shares * item.avg_cost;
                            return (
                              <tr key={item.ticker} className="border-b border-white/5 hover:bg-white/3 transition-colors">
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-2.5">
                                    <StockLogo ticker={item.ticker} size={28} />
                                    <span className="text-sm font-bold text-white">{item.ticker}</span>
                                  </div>
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-300 text-right tabular-nums font-bold">{item.shares}</td>
                                <td className="px-4 py-3 text-sm text-gray-300 text-right tabular-nums">${fmt(item.avg_cost)}</td>
                                <td className="px-4 py-3 text-sm text-white text-right tabular-nums font-bold">${fmt(item.price)}</td>
                                <td className="px-4 py-3 text-sm text-white text-right tabular-nums font-bold">${fmt(item.value)}</td>
                                <td className="px-4 py-3 text-right">
                                  <div className="flex items-center justify-end gap-2">
                                    <div className="w-16 h-1.5 rounded-full bg-white/10 overflow-hidden">
                                      <div
                                        className="h-full rounded-full bg-purple-400"
                                        style={{ width: `${Math.min(100, alloc)}%` }}
                                      />
                                    </div>
                                    <span className="text-xs text-gray-300 tabular-nums font-bold w-12 text-right">{alloc.toFixed(1)}%</span>
                                  </div>
                                </td>
                                <td className="px-4 py-3 text-right">
                                  <div>
                                    <span className="text-sm font-bold tabular-nums" style={{ color: item.pnl_pct >= 0 ? "#32D74B" : "#FF453A" }}>
                                      {fmtPct(item.pnl_pct)}
                                    </span>
                                    <span className="block text-[10px] tabular-nums" style={{ color: pnlVal >= 0 ? "rgba(50,215,75,0.6)" : "rgba(255,69,58,0.6)" }}>
                                      {pnlVal >= 0 ? "+" : ""}${fmt(Math.abs(pnlVal))}
                                    </span>
                                  </div>
                                </td>
                              </tr>
                            );
                          })}
                      </tbody>
                      <tfoot>
                        <tr className="bg-white/3">
                          <td className="px-4 py-3 text-sm font-black text-white" colSpan={4}>
                            {lang === "TH" ? "รวมทั้งหมด" : "Total"}
                          </td>
                          <td className="px-4 py-3 text-sm text-white text-right tabular-nums font-black">${fmt(total)}</td>
                          <td className="px-4 py-3 text-sm text-gray-400 text-right font-bold">100%</td>
                          <td className="px-4 py-3 text-right">
                            {(() => {
                              const totalCost = items.reduce((s, i) => s + i.shares * i.avg_cost, 0);
                              const totalPnl = total - totalCost;
                              const totalPnlPct = totalCost > 0 ? ((total - totalCost) / totalCost) * 100 : 0;
                              return (
                                <div>
                                  <span className="text-sm font-bold tabular-nums" style={{ color: totalPnl >= 0 ? "#32D74B" : "#FF453A" }}>
                                    {fmtPct(totalPnlPct)}
                                  </span>
                                  <span className="block text-[10px] tabular-nums" style={{ color: totalPnl >= 0 ? "rgba(50,215,75,0.6)" : "rgba(255,69,58,0.6)" }}>
                                    {totalPnl >= 0 ? "+" : ""}${fmt(Math.abs(totalPnl))}
                                  </span>
                                </div>
                              );
                            })()}
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {!loading && (
          <div className="px-6 py-4 border-t border-white/8 flex gap-3">
            <button onClick={onReanalyze}
              className="flex-1 py-3 bg-purple-500/15 text-purple-300 font-black rounded-xl hover:bg-purple-500/25 transition-colors text-sm flex items-center justify-center gap-2">
              <RefreshCw size={14} /> {lang === "TH" ? "วิเคราะห์ใหม่" : "Re-analyze"}
            </button>
            <button onClick={onClose}
              className="flex-1 py-3 bg-white/5 text-gray-300 font-bold rounded-xl hover:bg-white/10 transition-colors text-sm">
              {lang === "TH" ? "ปิด" : "Close"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
