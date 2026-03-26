"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useLang } from "@/lib/i18n";
import api from "@/lib/api";
import ProGate from "@/components/pro-gate";
import {
  createChart,
  LineSeries,
  type IChartApi,
  ColorType,
} from "lightweight-charts";
import { Swords, Loader2, TrendingUp, TrendingDown, Trophy } from "lucide-react";

function fmt(n: number) {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function pctColor(v: number) {
  return v >= 0 ? "#32D74B" : "#FF453A";
}

interface BenchData {
  labels: string[];
  portfolio_values: number[];
  benchmark_values: number[];
  benchmark_ticker: string;
  portfolio_metrics: Record<string, number>;
  benchmark_metrics: Record<string, number>;
}

const PERIODS = [
  { label: "1M", value: "1mo" },
  { label: "3M", value: "3mo" },
  { label: "6M", value: "6mo" },
  { label: "1Y", value: "1y" },
  { label: "2Y", value: "2y" },
  { label: "3Y", value: "3y" },
  { label: "5Y", value: "5y" },
];

const BENCHMARKS = ["SPY", "QQQ", "DIA", "IWM", "VOO"];

const CHART_OPTS = {
  layout: {
    background: { type: ColorType.Solid as const, color: "transparent" },
    textColor: "#8B949E",
    fontFamily: "Inter, system-ui, sans-serif",
    attributionLogo: false,
  },
  grid: {
    vertLines: { color: "rgba(255,255,255,0.03)" },
    horzLines: { color: "rgba(255,255,255,0.03)" },
  },
  timeScale: { borderColor: "rgba(255,255,255,0.08)", timeVisible: false },
  rightPriceScale: { borderColor: "rgba(255,255,255,0.08)" },
  crosshair: { mode: 0 },
};

export default function BenchmarkPage() {
  const { lang } = useLang();
  const [period, setPeriod] = useState("1y");
  const [bench, setBench] = useState("SPY");
  const [data, setData] = useState<BenchData | null>(null);
  const [loading, setLoading] = useState(true);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartApi = useRef<IChartApi | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const { data: res } = await api.get<BenchData>(
        `/api/market/benchmark?period=${period}&benchmark=${bench}`
      );
      setData(res);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [period, bench]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Chart rendering
  useEffect(() => {
    if (!chartRef.current || !data || !data.labels.length) return;

    if (chartApi.current) {
      chartApi.current.remove();
      chartApi.current = null;
    }

    const chart = createChart(chartRef.current, {
      ...CHART_OPTS,
      width: chartRef.current.clientWidth,
      height: 380,
    });
    chartApi.current = chart;

    const portfolioSeries = chart.addSeries(LineSeries, {
      color: "#D0FD3E",
      lineWidth: 2,
      title: "Portfolio",
    });

    const benchSeries = chart.addSeries(LineSeries, {
      color: "#39C8FF",
      lineWidth: 2,
      lineStyle: 2,
      title: data.benchmark_ticker,
    });

    const pData = data.labels.map((d, i) => ({
      time: d as string,
      value: data.portfolio_values[i],
    }));
    const bData = data.labels.map((d, i) => ({
      time: d as string,
      value: data.benchmark_values[i],
    }));

    portfolioSeries.setData(pData);
    if (bData.length) benchSeries.setData(bData);
    chart.timeScale().fitContent();

    const ro = new ResizeObserver(([e]) => {
      chart.applyOptions({ width: e.contentRect.width });
    });
    ro.observe(chartRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
      chartApi.current = null;
    };
  }, [data]);

  const pm = data?.portfolio_metrics || {};
  const bm = data?.benchmark_metrics || {};
  const pReturn = pm.total_return_pct || 0;
  const bReturn = bm.total_return_pct || 0;
  const alpha = pReturn - bReturn;
  const portfolioWins = pReturn > bReturn;

  return (
    <ProGate>
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-5">
          <h1
            className="text-2xl font-black tracking-wide flex items-center gap-3"
            style={{ color: "var(--text-primary)" }}
          >
            <Swords className="text-[#39C8FF]" size={24} />
            {lang === "TH" ? "เทียบ Benchmark" : "Portfolio vs Benchmark"}
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            {lang === "TH"
              ? "เปรียบเทียบผลตอบแทนพอร์ตกับดัชนีอ้างอิง"
              : "Compare your portfolio performance against market indices"}
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3 mb-5">
          {/* Period */}
          <div className="flex gap-1">
            {PERIODS.map((p) => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  period === p.value
                    ? "bg-[#D0FD3E]/15 border border-[#D0FD3E]/30 text-[#D0FD3E]"
                    : "text-gray-500 hover:text-white hover:bg-white/5 border border-transparent"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Benchmark selector */}
          <div className="flex gap-1 ml-auto">
            {BENCHMARKS.map((b) => (
              <button
                key={b}
                onClick={() => setBench(b)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  bench === b
                    ? "bg-[#39C8FF]/15 border border-[#39C8FF]/30 text-[#39C8FF]"
                    : "text-gray-500 hover:text-white hover:bg-white/5 border border-transparent"
                }`}
              >
                {b}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
          </div>
        ) : !data || !data.labels.length ? (
          <div
            className="border rounded-2xl p-12 text-center"
            style={{
              background: "var(--bg-card)",
              borderColor: "var(--border-default)",
            }}
          >
            <Swords className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p
              className="text-lg font-bold"
              style={{ color: "var(--text-primary)" }}
            >
              {lang === "TH"
                ? "ยังไม่มีข้อมูลเปรียบเทียบ"
                : "No benchmark data available"}
            </p>
            <p className="text-sm mt-2" style={{ color: "var(--text-muted)" }}>
              {lang === "TH"
                ? "เพิ่มหุ้นในพอร์ตเพื่อเปรียบเทียบผลตอบแทน"
                : "Add stocks to your portfolio to compare performance"}
            </p>
          </div>
        ) : (
          <>
            {/* Score cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
              {/* Portfolio Return */}
              <div
                className="border rounded-2xl p-4"
                style={{
                  background: "var(--bg-card)",
                  borderColor: "var(--border-default)",
                }}
              >
                <p
                  className="text-[10px] uppercase tracking-wider font-bold mb-1"
                  style={{ color: "var(--text-dim)" }}
                >
                  {lang === "TH" ? "ผลตอบแทนพอร์ต" : "Portfolio Return"}
                </p>
                <div className="flex items-center gap-1.5">
                  {pReturn >= 0 ? (
                    <TrendingUp size={16} style={{ color: pctColor(pReturn) }} />
                  ) : (
                    <TrendingDown size={16} style={{ color: pctColor(pReturn) }} />
                  )}
                  <span
                    className="text-xl font-black tabular-nums"
                    style={{ color: pctColor(pReturn) }}
                  >
                    {pReturn >= 0 ? "+" : ""}
                    {pReturn.toFixed(2)}%
                  </span>
                </div>
              </div>

              {/* Benchmark Return */}
              <div
                className="border rounded-2xl p-4"
                style={{
                  background: "var(--bg-card)",
                  borderColor: "var(--border-default)",
                }}
              >
                <p
                  className="text-[10px] uppercase tracking-wider font-bold mb-1"
                  style={{ color: "var(--text-dim)" }}
                >
                  {data.benchmark_ticker} Return
                </p>
                <div className="flex items-center gap-1.5">
                  {bReturn >= 0 ? (
                    <TrendingUp size={16} style={{ color: pctColor(bReturn) }} />
                  ) : (
                    <TrendingDown size={16} style={{ color: pctColor(bReturn) }} />
                  )}
                  <span
                    className="text-xl font-black tabular-nums"
                    style={{ color: pctColor(bReturn) }}
                  >
                    {bReturn >= 0 ? "+" : ""}
                    {bReturn.toFixed(2)}%
                  </span>
                </div>
              </div>

              {/* Alpha */}
              <div
                className="border rounded-2xl p-4"
                style={{
                  background: "var(--bg-card)",
                  borderColor: "var(--border-default)",
                }}
              >
                <p
                  className="text-[10px] uppercase tracking-wider font-bold mb-1"
                  style={{ color: "var(--text-dim)" }}
                >
                  Alpha
                </p>
                <span
                  className="text-xl font-black tabular-nums"
                  style={{ color: pctColor(alpha) }}
                >
                  {alpha >= 0 ? "+" : ""}
                  {alpha.toFixed(2)}%
                </span>
              </div>

              {/* Winner */}
              <div
                className="border rounded-2xl p-4 flex items-center gap-3"
                style={{
                  background: portfolioWins
                    ? "rgba(208,253,62,0.08)"
                    : "rgba(57,200,255,0.08)",
                  borderColor: portfolioWins
                    ? "rgba(208,253,62,0.2)"
                    : "rgba(57,200,255,0.2)",
                }}
              >
                <Trophy
                  size={22}
                  style={{
                    color: portfolioWins ? "#D0FD3E" : "#39C8FF",
                  }}
                />
                <div>
                  <p
                    className="text-[10px] uppercase tracking-wider font-bold"
                    style={{ color: "var(--text-dim)" }}
                  >
                    {lang === "TH" ? "ผู้ชนะ" : "Winner"}
                  </p>
                  <p
                    className="font-black text-sm"
                    style={{
                      color: portfolioWins ? "#D0FD3E" : "#39C8FF",
                    }}
                  >
                    {portfolioWins
                      ? lang === "TH"
                        ? "พอร์ตคุณ"
                        : "Your Portfolio"
                      : data.benchmark_ticker}
                  </p>
                </div>
              </div>
            </div>

            {/* Chart */}
            <div
              className="border rounded-2xl p-4 mb-5"
              style={{
                background: "var(--bg-card)",
                borderColor: "var(--border-default)",
              }}
            >
              <div className="flex items-center gap-4 mb-3 text-xs">
                <div className="flex items-center gap-1.5">
                  <div
                    className="w-4 h-0.5 rounded"
                    style={{ background: "#D0FD3E" }}
                  />
                  <span style={{ color: "var(--text-muted)" }}>
                    {lang === "TH" ? "พอร์ตของฉัน" : "My Portfolio"}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div
                    className="w-4 h-0.5 rounded"
                    style={{
                      background: "#39C8FF",
                      borderTop: "1px dashed #39C8FF",
                    }}
                  />
                  <span style={{ color: "var(--text-muted)" }}>
                    {data.benchmark_ticker}
                  </span>
                </div>
              </div>
              <div ref={chartRef} />
            </div>

            {/* Metrics table */}
            <div
              className="border rounded-2xl overflow-hidden"
              style={{
                background: "var(--bg-card)",
                borderColor: "var(--border-default)",
              }}
            >
              <div
                className="px-4 py-3"
                style={{
                  borderBottom: "1px solid var(--border-default)",
                }}
              >
                <span
                  className="text-xs font-black tracking-widest uppercase"
                  style={{ color: "var(--text-muted)" }}
                >
                  {lang === "TH" ? "ตัวชี้วัด" : "PERFORMANCE METRICS"}
                </span>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr
                    style={{
                      borderBottom: "1px solid var(--border-subtle)",
                    }}
                  >
                    <th
                      className="px-4 py-2.5 text-left text-[10px] font-black tracking-wider uppercase"
                      style={{ color: "var(--text-dim)" }}
                    >
                      Metric
                    </th>
                    <th
                      className="px-4 py-2.5 text-right text-[10px] font-black tracking-wider uppercase"
                      style={{ color: "#D0FD3E" }}
                    >
                      {lang === "TH" ? "พอร์ต" : "Portfolio"}
                    </th>
                    <th
                      className="px-4 py-2.5 text-right text-[10px] font-black tracking-wider uppercase"
                      style={{ color: "#39C8FF" }}
                    >
                      {data.benchmark_ticker}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["Total Return", "total_return_pct", "%"],
                    ["Annualized", "annualized_return_pct", "%"],
                    ["Max Drawdown", "max_drawdown_pct", "%"],
                    ["Volatility", "volatility_pct", "%"],
                    ["Sharpe Ratio", "sharpe_ratio", ""],
                  ].map(([label, key, suffix]) => (
                    <tr
                      key={key}
                      style={{
                        borderBottom: "1px solid var(--border-subtle)",
                      }}
                    >
                      <td
                        className="px-4 py-3 font-bold"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {label}
                      </td>
                      <td
                        className="px-4 py-3 text-right tabular-nums font-black"
                        style={{
                          color:
                            key.includes("drawdown")
                              ? "#FF453A"
                              : "var(--text-primary)",
                        }}
                      >
                        {pm[key] !== undefined
                          ? `${fmt(pm[key])}${suffix}`
                          : "—"}
                      </td>
                      <td
                        className="px-4 py-3 text-right tabular-nums font-black"
                        style={{
                          color:
                            key.includes("drawdown")
                              ? "#FF453A"
                              : "var(--text-primary)",
                        }}
                      >
                        {bm[key] !== undefined
                          ? `${fmt(bm[key])}${suffix}`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </ProGate>
  );
}
