"use client";

import { useMacro } from "@/lib/hooks";
import ProGate from "@/components/pro-gate";
import {
  Globe,
  Loader2,
  Activity,
  TrendingUp,
  TrendingDown,
  Gauge,
  BarChart3,
  RefreshCw,
} from "lucide-react";

function fgColor(value: number): string {
  if (value <= 25) return "#FF453A";
  if (value <= 45) return "#FF9500";
  if (value <= 55) return "#FCD535";
  if (value <= 75) return "#32D74B";
  return "#00C853";
}

function vixColor(vix: number): string {
  if (vix < 15) return "#32D74B";
  if (vix < 20) return "#FCD535";
  if (vix < 30) return "#FF9500";
  return "#FF453A";
}

function vixLabel(vix: number): string {
  if (vix < 15) return "Low Volatility";
  if (vix < 20) return "Normal";
  if (vix < 30) return "Elevated";
  return "High Fear";
}

export default function MacroPage() {
  const { data, loading, refresh } = useMacro();

  return (
    <ProGate>
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-black text-white tracking-wide flex items-center gap-3">
            <Globe className="text-[#39C8FF]" size={24} />
            Macro HUD
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Global market risk dashboard
          </p>
        </div>
        <button
          onClick={refresh}
          className="flex items-center gap-1.5 px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
        </div>
      ) : !data ? (
        <div className="text-center py-16 text-gray-500">
          Failed to load macro data
        </div>
      ) : (
        <div className="space-y-6">
          {/* Fear & Greed + VIX row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Fear & Greed */}
            <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 rounded-full blur-[80px] pointer-events-none"
                style={{ background: `${fgColor(data.fear_greed.value)}20` }} />
              <div className="flex items-center gap-2 mb-4">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: `${fgColor(data.fear_greed.value)}15` }}>
                  <Gauge size={20} style={{ color: fgColor(data.fear_greed.value) }} />
                </div>
                <div>
                  <span className="text-xs text-gray-500 font-bold uppercase tracking-wider">
                    Fear & Greed Index
                  </span>
                </div>
              </div>
              <div className="flex items-end gap-3 mb-3">
                <span className="text-5xl font-black tabular-nums"
                  style={{ color: fgColor(data.fear_greed.value) }}>
                  {data.fear_greed.value}
                </span>
                <span className="text-lg font-bold mb-1"
                  style={{ color: fgColor(data.fear_greed.value) }}>
                  {data.fear_greed.text}
                </span>
              </div>
              {/* Gauge bar */}
              <div className="h-3 bg-white/5 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-1000"
                  style={{
                    width: `${data.fear_greed.value}%`,
                    background: `linear-gradient(90deg, #FF453A, #FF9500, #FCD535, #32D74B, #00C853)`,
                  }} />
              </div>
              <div className="flex justify-between mt-1 text-[10px] text-gray-600">
                <span>Extreme Fear</span>
                <span>Extreme Greed</span>
              </div>
            </div>

            {/* VIX */}
            <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 rounded-full blur-[80px] pointer-events-none"
                style={{ background: `${vixColor(data.vix)}20` }} />
              <div className="flex items-center gap-2 mb-4">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: `${vixColor(data.vix)}15` }}>
                  <Activity size={20} style={{ color: vixColor(data.vix) }} />
                </div>
                <div>
                  <span className="text-xs text-gray-500 font-bold uppercase tracking-wider">
                    VIX (Volatility Index)
                  </span>
                </div>
              </div>
              <div className="flex items-end gap-3 mb-3">
                <span className="text-5xl font-black tabular-nums"
                  style={{ color: vixColor(data.vix) }}>
                  {data.vix.toFixed(2)}
                </span>
                <span className="text-lg font-bold mb-1"
                  style={{ color: vixColor(data.vix) }}>
                  {vixLabel(data.vix)}
                </span>
              </div>
              <div className="h-3 bg-white/5 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-1000"
                  style={{
                    width: `${Math.min(data.vix / 50 * 100, 100)}%`,
                    background: vixColor(data.vix),
                  }} />
              </div>
              <div className="flex justify-between mt-1 text-[10px] text-gray-600">
                <span>Low</span>
                <span>Extreme</span>
              </div>
            </div>
          </div>

          {/* Market Indices */}
          <div className="bg-[#0D1117] border border-white/8 rounded-2xl overflow-hidden">
            <div className="px-5 py-3 border-b border-white/5">
              <h2 className="text-sm font-black text-white tracking-wider flex items-center gap-2">
                <BarChart3 size={16} className="text-[#D0FD3E]" />
                Market Indices
              </h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
              {Object.entries(data.indices).map(([symbol, info]) => (
                <div key={symbol} className="p-4 border-b border-r border-white/5 last:border-r-0">
                  <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block mb-1">
                    {info.name}
                  </span>
                  <span className="text-white font-mono font-bold text-lg tabular-nums">
                    {info.price > 1000
                      ? info.price.toLocaleString("en-US", { maximumFractionDigits: 0 })
                      : info.price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Sector Rotation */}
          {data.sectors && Object.keys(data.sectors).length > 0 && (
            <div className="bg-[#0D1117] border border-white/8 rounded-2xl overflow-hidden">
              <div className="px-5 py-3 border-b border-white/5">
                <h2 className="text-sm font-black text-white tracking-wider flex items-center gap-2">
                  <TrendingUp size={16} className="text-[#32D74B]" />
                  Sector Performance
                </h2>
              </div>
              <div className="p-5 space-y-3">
                {Object.entries(data.sectors)
                  .sort(([, a], [, b]) => Number(b) - Number(a))
                  .map(([sector, rawPerf]) => {
                    const performance = Number(rawPerf) || 0;
                    const up = performance >= 0;
                    return (
                      <div key={sector} className="flex items-center gap-3">
                        <span className="text-sm text-gray-400 w-40 truncate font-bold">
                          {sector}
                        </span>
                        <div className="flex-1 h-6 bg-white/5 rounded-lg overflow-hidden relative">
                          <div
                            className="h-full rounded-lg transition-all duration-500"
                            style={{
                              width: `${Math.min(Math.abs(performance) * 5, 100)}%`,
                              background: up ? "rgba(50,215,75,0.3)" : "rgba(255,69,58,0.3)",
                            }}
                          />
                        </div>
                        <div className="flex items-center gap-1 w-20 justify-end">
                          {up ? (
                            <TrendingUp size={12} className="text-[#32D74B]" />
                          ) : (
                            <TrendingDown size={12} className="text-[#FF453A]" />
                          )}
                          <span
                            className="text-sm font-mono font-bold tabular-nums"
                            style={{ color: up ? "#32D74B" : "#FF453A" }}
                          >
                            {up ? "+" : ""}
                            {performance.toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
    </ProGate>
  );
}
