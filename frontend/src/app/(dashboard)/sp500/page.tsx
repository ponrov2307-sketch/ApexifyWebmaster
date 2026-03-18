"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { useLang } from "@/lib/i18n";
import ProGate from "@/components/pro-gate";
import {
  createChart,
  LineSeries,
  type IChartApi,
  ColorType,
} from "lightweight-charts";
import {
  TrendingUp,
  Loader2,
  Swords,
  Trophy,
} from "lucide-react";

function fmt(n: number) {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

interface DuelResult {
  ticker1: { ticker: string; startPrice: number; endPrice: number; returnPct: number };
  ticker2: { ticker: string; startPrice: number; endPrice: number; returnPct: number };
}

interface CandleData {
  date: string;
  close: number;
}

const PERIODS = [
  { label: "1M", value: "1mo" },
  { label: "3M", value: "3mo" },
  { label: "6M", value: "6mo" },
  { label: "1Y", value: "1y" },
  { label: "5Y", value: "5y" },
  { label: "10Y", value: "10y" },
  { label: "20Y", value: "20y" },
  { label: "MAX", value: "max" },
];

const CHART_OPTS = {
  layout: {
    background: { type: ColorType.Solid as const, color: "transparent" },
    textColor: "#8B949E",
    fontFamily: "Inter, system-ui, sans-serif",
    attributionLogo: false,
  },
  grid: {
    vertLines: { color: "rgba(255,255,255,0.04)" },
    horzLines: { color: "rgba(255,255,255,0.04)" },
  },
  rightPriceScale: { borderColor: "rgba(255,255,255,0.08)" },
  crosshair: {
    horzLine: { color: "rgba(208,253,62,0.3)", labelBackgroundColor: "#D0FD3E" },
    vertLine: { color: "rgba(208,253,62,0.3)", labelBackgroundColor: "#D0FD3E" },
  },
};

export default function SimulatorPage() {
  const { lang } = useLang();
  const [ticker1, setTicker1] = useState("");
  const [ticker2, setTicker2] = useState("");
  const [period, setPeriod] = useState("1y");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DuelResult | null>(null);
  const [error, setError] = useState("");
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<IChartApi | null>(null);
  const [candles1, setCandles1] = useState<CandleData[]>([]);
  const [candles2, setCandles2] = useState<CandleData[]>([]);

  const handleDuel = useCallback(async () => {
    if (!ticker1.trim() || !ticker2.trim()) {
      setError(lang === "TH" ? "กรุณาใส่ทั้ง 2 ตัว" : "Enter both tickers");
      return;
    }
    setError("");
    setLoading(true);
    setResult(null);

    try {
      const [{ data: data1 }, { data: data2 }] = await Promise.all([
        api.get(`/api/market/chart/${ticker1.trim().toUpperCase()}?period=${period}`),
        api.get(`/api/market/chart/${ticker2.trim().toUpperCase()}?period=${period}`),
      ]);

      const c1: CandleData[] = data1.candles || [];
      const c2: CandleData[] = data2.candles || [];

      if (c1.length < 2 || c2.length < 2) {
        setError(lang === "TH" ? "ข้อมูลไม่เพียงพอ" : "Not enough data for comparison");
        return;
      }

      setCandles1(c1);
      setCandles2(c2);

      const start1 = c1[0].close;
      const end1 = c1[c1.length - 1].close;
      const start2 = c2[0].close;
      const end2 = c2[c2.length - 1].close;

      setResult({
        ticker1: {
          ticker: ticker1.trim().toUpperCase(),
          startPrice: start1,
          endPrice: end1,
          returnPct: ((end1 - start1) / start1) * 100,
        },
        ticker2: {
          ticker: ticker2.trim().toUpperCase(),
          startPrice: start2,
          endPrice: end2,
          returnPct: ((end2 - start2) / start2) * 100,
        },
      });
    } catch {
      setError(lang === "TH" ? "ไม่สามารถดึงข้อมูลได้" : "Failed to fetch data. Check tickers and try again.");
    } finally {
      setLoading(false);
    }
  }, [ticker1, ticker2, period, lang]);

  // Render comparison chart
  useEffect(() => {
    if (!result || !chartRef.current || candles1.length === 0 || candles2.length === 0) return;

    chartInstance.current?.remove();

    const chart = createChart(chartRef.current, {
      ...CHART_OPTS,
      height: 400,
      timeScale: { borderColor: "rgba(255,255,255,0.08)", timeVisible: false },
    });
    chartInstance.current = chart;

    // Normalize to percentage returns from start
    const base1 = candles1[0].close;
    const base2 = candles2[0].close;

    chart.addSeries(LineSeries, {
      color: "#D0FD3E",
      lineWidth: 2,
      priceFormat: { type: "custom", formatter: (v: number) => `${v >= 0 ? "+" : ""}${v.toFixed(1)}%` },
      title: result.ticker1.ticker,
    }).setData(
      candles1.map((c) => ({
        time: c.date as string,
        value: ((c.close - base1) / base1) * 100,
      })),
    );

    chart.addSeries(LineSeries, {
      color: "#56D3FF",
      lineWidth: 2,
      priceFormat: { type: "custom", formatter: (v: number) => `${v >= 0 ? "+" : ""}${v.toFixed(1)}%` },
      title: result.ticker2.ticker,
    }).setData(
      candles2.map((c) => ({
        time: c.date as string,
        value: ((c.close - base2) / base2) * 100,
      })),
    );

    // Zero line
    chart.addSeries(LineSeries, {
      color: "rgba(255,255,255,0.1)",
      lineWidth: 1,
      lineStyle: 2,
      lastValueVisible: false,
      priceLineVisible: false,
    }).setData(
      candles1.map((c) => ({ time: c.date as string, value: 0 })),
    );

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth });
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartInstance.current = null;
    };
  }, [result, candles1, candles2]);

  const winner = result
    ? result.ticker1.returnPct > result.ticker2.returnPct
      ? result.ticker1
      : result.ticker2
    : null;

  return (
    <ProGate>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-black text-white tracking-wide flex items-center gap-3">
            <Swords className="text-[#FF9500]" size={24} />
            Stock Duel
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            {lang === "TH" ? "เปรียบเทียบผลตอบแทนสองหุ้นแบบกราฟ" : "Compare two stocks head-to-head with charts"}
          </p>
        </div>

        {/* Input form */}
        <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-5 mb-6">
          <div className="flex flex-col sm:flex-row items-end gap-3">
            <div className="flex-1 w-full">
              <label className="block text-xs text-gray-400 mb-1 font-bold uppercase tracking-wider">
                Stock 1
              </label>
              <input
                type="text"
                placeholder="AAPL"
                value={ticker1}
                onChange={(e) => setTicker1(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleDuel()}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-gray-600 outline-none focus:border-[#D0FD3E]/40 uppercase"
              />
            </div>
            <div className="hidden sm:flex items-center pb-2">
              <Swords size={20} className="text-gray-600" />
            </div>
            <div className="flex-1 w-full">
              <label className="block text-xs text-gray-400 mb-1 font-bold uppercase tracking-wider">
                Stock 2
              </label>
              <input
                type="text"
                placeholder="MSFT"
                value={ticker2}
                onChange={(e) => setTicker2(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleDuel()}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-gray-600 outline-none focus:border-[#56D3FF]/40 uppercase"
              />
            </div>
          </div>

          {/* Period selector */}
          <div className="flex flex-wrap items-center gap-2 mt-4">
            <span className="text-xs text-gray-500 font-bold mr-1">Period:</span>
            {PERIODS.map((p) => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
                  period === p.value
                    ? "bg-[#D0FD3E] text-[#080B10]"
                    : "text-gray-400 hover:text-white hover:bg-white/5"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {error && <p className="text-sm text-[#FF453A] mt-3">{error}</p>}

          <button
            onClick={handleDuel}
            disabled={loading}
            className="w-full mt-4 py-3 bg-[#D0FD3E] hover:bg-[#c5f232] text-[#080B10] font-black rounded-xl transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <>
                <Swords size={16} />
                {lang === "TH" ? "เปรียบเทียบ" : "Compare"}
              </>
            )}
          </button>
        </div>

        {/* Chart */}
        {result && (
          <div className="space-y-4">
            {/* Performance chart */}
            <div className="bg-[#0D1117] border border-white/8 rounded-2xl overflow-hidden">
              <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-0.5 bg-[#D0FD3E] rounded" />
                    <span className="text-xs font-bold text-white">{result.ticker1.ticker}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-0.5 bg-[#56D3FF] rounded" />
                    <span className="text-xs font-bold text-white">{result.ticker2.ticker}</span>
                  </div>
                </div>
                <span className="text-[10px] text-gray-500 font-bold">
                  {PERIODS.find((p) => p.value === period)?.label}{" "}
                  {lang === "TH" ? "ผลตอบแทน %" : "Return %"}
                </span>
              </div>
              <div ref={chartRef} className="w-full" />
            </div>

            {/* Score cards */}
            <div className="grid grid-cols-2 gap-4">
              {[result.ticker1, result.ticker2].map((stock, idx) => {
                const isWinner = winner?.ticker === stock.ticker;
                const color = idx === 0 ? "#D0FD3E" : "#56D3FF";
                const up = stock.returnPct >= 0;
                return (
                  <div
                    key={stock.ticker}
                    className={`bg-[#0D1117] border rounded-2xl p-5 relative overflow-hidden transition-all ${
                      isWinner ? "border-[#32D74B]/40 shadow-[0_0_20px_rgba(50,215,75,0.1)]" : "border-white/8"
                    }`}
                  >
                    {isWinner && (
                      <div className="absolute top-3 right-3">
                        <div className="flex items-center gap-1 px-2 py-0.5 bg-[#32D74B]/20 text-[#32D74B] rounded-full text-[10px] font-black">
                          <Trophy size={10} /> WINNER
                        </div>
                      </div>
                    )}
                    <div className="flex items-center gap-2 mb-4">
                      <div className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-black text-white" style={{ background: `${color}15`, border: `1px solid ${color}30` }}>
                        {stock.ticker.slice(0, 2)}
                      </div>
                      <span className="text-xl font-black text-white">{stock.ticker}</span>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">{lang === "TH" ? "ราคาเริ่ม" : "Start"}</span>
                        <span className="text-white font-mono tabular-nums">${fmt(stock.startPrice)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">{lang === "TH" ? "ราคาปัจจุบัน" : "End"}</span>
                        <span className="text-white font-mono tabular-nums">${fmt(stock.endPrice)}</span>
                      </div>
                      <div className="flex justify-between pt-2 border-t border-white/5">
                        <span className="text-gray-500 font-bold">{lang === "TH" ? "ผลตอบแทน" : "Return"}</span>
                        <span
                          className="text-xl font-black tabular-nums"
                          style={{ color: up ? "#32D74B" : "#FF453A" }}
                        >
                          {up ? "+" : ""}{stock.returnPct.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </ProGate>
  );
}
