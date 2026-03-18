"use client";

import { useState } from "react";
import { usePortfolio } from "@/lib/hooks";
import ProGate from "@/components/pro-gate";
import {
  Download,
  FileSpreadsheet,
  FileText,
  Loader2,
  Check,
} from "lucide-react";

function fmt(n: number) {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function ExportPage() {
  const { items, summary, loading } = usePortfolio();
  const [exported, setExported] = useState<string | null>(null);

  const exportCSV = () => {
    if (!items.length) return;
    const headers = ["Ticker", "Shares", "Avg Cost", "Price", "Value", "P&L", "P&L %", "Group"];
    const rows = items.map((i) => [
      i.ticker,
      i.shares,
      i.avg_cost.toFixed(2),
      i.price.toFixed(2),
      i.value.toFixed(2),
      i.pnl.toFixed(2),
      i.pnl_pct.toFixed(2) + "%",
      i.asset_group,
    ]);

    const csv = [headers, ...rows].map((row) => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `apexify-portfolio-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    setExported("csv");
    setTimeout(() => setExported(null), 2000);
  };

  const exportJSON = () => {
    if (!items.length) return;
    const data = {
      exported_at: new Date().toISOString(),
      summary,
      holdings: items,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `apexify-portfolio-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setExported("json");
    setTimeout(() => setExported(null), 2000);
  };

  return (
    <ProGate>
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-black text-white tracking-wide flex items-center gap-3">
          <Download className="text-[#AF52DE]" size={24} />
          Export Data
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Download your portfolio data in various formats
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
        </div>
      ) : items.length === 0 ? (
        <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-12 text-center">
          <Download className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h2 className="text-lg font-bold text-white mb-2">Nothing to export</h2>
          <p className="text-gray-500 text-sm">Add stocks to your portfolio first</p>
        </div>
      ) : (
        <>
          {/* Export cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            <button
              onClick={exportCSV}
              className="bg-[#0D1117] border border-white/8 rounded-2xl p-6 text-left hover:border-[#32D74B]/30 transition-colors group"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-12 h-12 rounded-xl bg-[#32D74B]/10 flex items-center justify-center">
                  {exported === "csv" ? (
                    <Check size={24} className="text-[#32D74B]" />
                  ) : (
                    <FileSpreadsheet size={24} className="text-[#32D74B]" />
                  )}
                </div>
                <div>
                  <span className="text-white font-black block">CSV</span>
                  <span className="text-gray-500 text-xs">Spreadsheet format</span>
                </div>
              </div>
              <p className="text-gray-400 text-sm">
                Compatible with Excel, Google Sheets, and other spreadsheet apps.
              </p>
            </button>

            <button
              onClick={exportJSON}
              className="bg-[#0D1117] border border-white/8 rounded-2xl p-6 text-left hover:border-[#39C8FF]/30 transition-colors group"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-12 h-12 rounded-xl bg-[#39C8FF]/10 flex items-center justify-center">
                  {exported === "json" ? (
                    <Check size={24} className="text-[#39C8FF]" />
                  ) : (
                    <FileText size={24} className="text-[#39C8FF]" />
                  )}
                </div>
                <div>
                  <span className="text-white font-black block">JSON</span>
                  <span className="text-gray-500 text-xs">Developer format</span>
                </div>
              </div>
              <p className="text-gray-400 text-sm">
                Full data with summary, holdings, and metadata for programmatic use.
              </p>
            </button>
          </div>

          {/* Preview */}
          <div className="bg-[#0D1117] border border-white/8 rounded-2xl overflow-hidden">
            <div className="px-5 py-3 border-b border-white/5">
              <h2 className="text-sm font-black text-white tracking-wider">Data Preview</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/8 text-gray-500 text-xs uppercase tracking-wider">
                    <th className="text-left px-4 py-2 font-bold">Ticker</th>
                    <th className="text-right px-4 py-2 font-bold">Shares</th>
                    <th className="text-right px-4 py-2 font-bold">Avg Cost</th>
                    <th className="text-right px-4 py-2 font-bold">Price</th>
                    <th className="text-right px-4 py-2 font-bold">Value</th>
                    <th className="text-right px-4 py-2 font-bold">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((i) => (
                    <tr key={i.ticker} className="border-b border-white/5">
                      <td className="px-4 py-2 font-bold text-white">{i.ticker}</td>
                      <td className="text-right px-4 py-2 text-gray-400">{i.shares}</td>
                      <td className="text-right px-4 py-2 text-gray-400 font-mono tabular-nums">${fmt(i.avg_cost)}</td>
                      <td className="text-right px-4 py-2 text-white font-mono tabular-nums">${fmt(i.price)}</td>
                      <td className="text-right px-4 py-2 text-white font-mono tabular-nums">${fmt(i.value)}</td>
                      <td className="text-right px-4 py-2 font-mono font-bold tabular-nums"
                        style={{ color: i.pnl >= 0 ? "#32D74B" : "#FF453A" }}>
                        {i.pnl >= 0 ? "+" : ""}{fmt(i.pnl)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {summary && (
              <div className="px-4 py-2 border-t border-white/8 text-xs text-gray-500">
                {items.length} stocks &middot; Total: ${fmt(summary.total_value)} &middot; P&L: ${fmt(summary.total_pnl)}
              </div>
            )}
          </div>
        </>
      )}
    </div>
    </ProGate>
  );
}
