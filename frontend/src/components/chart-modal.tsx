"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  type IChartApi,
  ColorType,
} from "lightweight-charts";
import { X, Loader2, BarChart3, Activity, TrendingUp, Waves, Info } from "lucide-react";
import { logoUrl } from "@/lib/dashboard-helpers";
import api from "@/lib/api";

interface Props {
  ticker: string;
  open: boolean;
  onClose: () => void;
}

const PERIODS = [
  { label: "1M", value: "1mo" },
  { label: "3M", value: "3mo" },
  { label: "6M", value: "6mo" },
  { label: "1Y", value: "1y" },
  { label: "2Y", value: "2y" },
  { label: "5Y", value: "5y" },
  { label: "10Y", value: "10y" },
  { label: "20Y", value: "20y" },
  { label: "MAX", value: "max" },
];

interface CandleData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface ChartData {
  candles: CandleData[];
  indicators: {
    rsi?: (number | string)[];
    macd?: {
      macd: (number | string)[];
      signal: (number | string)[];
      histogram: (number | string)[];
    };
    bollinger?: [(number | string)[], (number | string)[], (number | string)[]];
  };
}

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
  crosshair: {
    horzLine: { color: "rgba(208,253,62,0.3)", labelBackgroundColor: "#D0FD3E" },
    vertLine: { color: "rgba(208,253,62,0.3)", labelBackgroundColor: "#D0FD3E" },
  },
  rightPriceScale: { borderColor: "rgba(255,255,255,0.08)" },
};

function calcSMA(closes: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else {
      let sum = 0;
      for (let j = i - period + 1; j <= i; j++) sum += closes[j];
      result.push(sum / period);
    }
  }
  return result;
}

function calcEMA(closes: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  const k = 2 / (period + 1);
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else if (i === period - 1) {
      let sum = 0;
      for (let j = 0; j < period; j++) sum += closes[j];
      result.push(sum / period);
    } else {
      const prev = result[i - 1];
      if (prev !== null) {
        result.push(closes[i] * k + prev * (1 - k));
      } else {
        result.push(null);
      }
    }
  }
  return result;
}

interface StockInfo {
  price: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  market_cap: number;
  pe_ratio: number;
  div_yield: number;
  name: string;
  "52w_high": number;
  "52w_low": number;
}

export default function ChartModal({ ticker, open, onClose }: Props) {
  const mainRef = useRef<HTMLDivElement>(null);
  const rsiRef = useRef<HTMLDivElement>(null);
  const macdRef = useRef<HTMLDivElement>(null);
  const mainChart = useRef<IChartApi | null>(null);
  const rsiChart = useRef<IChartApi | null>(null);
  const macdChart = useRef<IChartApi | null>(null);

  const [period, setPeriod] = useState("3mo");
  const [loading, setLoading] = useState(false);
  const [showRsi, setShowRsi] = useState(false);
  const [showMacd, setShowMacd] = useState(false);
  const [showBollinger, setShowBollinger] = useState(false);
  const [showMA, setShowMA] = useState(false);
  const [showEMA, setShowEMA] = useState(false);
  const [showVWAP, setShowVWAP] = useState(false);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [priceChange, setPriceChange] = useState(0);
  const [showInfo, setShowInfo] = useState(true);
  const [stockInfo, setStockInfo] = useState<StockInfo | null>(null);

  // Fetch stock info for left panel
  useEffect(() => {
    if (!open) return;
    (async () => {
      try {
        const { data } = await api.get(`/api/market/price/${ticker}`);
        // Get additional info
        setStockInfo({
          price: data.price || 0,
          open: 0, high: 0, low: 0, volume: 0, market_cap: 0,
          pe_ratio: 0, div_yield: 0, name: ticker,
          "52w_high": 0, "52w_low": 0,
        });
      } catch { /* */ }
    })();
  }, [open, ticker]);

  // Fetch chart data
  const fetchData = useCallback(async () => {
    if (!open) return;
    setLoading(true);
    try {
      const { data } = await api.get(
        `/api/market/chart/${ticker}?period=${period}&indicators=rsi,macd,bollinger`,
      );
      setChartData(data);
      const candles: CandleData[] = data.candles || [];
      if (candles.length > 0) {
        const last = candles[candles.length - 1];
        const first = candles[0];
        setCurrentPrice(last.close);
        setPriceChange(first.close > 0 ? ((last.close - first.close) / first.close) * 100 : 0);
      }
    } catch { /* */ }
    finally { setLoading(false); }
  }, [open, ticker, period]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Render charts
  useEffect(() => {
    if (!chartData || !mainRef.current) return;
    const candles = chartData.candles;
    if (!candles?.length) return;

    mainChart.current?.remove(); mainChart.current = null;
    rsiChart.current?.remove(); rsiChart.current = null;
    macdChart.current?.remove(); macdChart.current = null;

    const mc = createChart(mainRef.current, {
      ...CHART_OPTS,
      timeScale: { borderColor: "rgba(255,255,255,0.08)", timeVisible: true, rightOffset: 5, barSpacing: 6, minBarSpacing: 2 },
    });
    mainChart.current = mc;

    mc.addSeries(CandlestickSeries, {
      upColor: "#32D74B", downColor: "#FF453A",
      borderUpColor: "#32D74B", borderDownColor: "#FF453A",
      wickUpColor: "#32D74B", wickDownColor: "#FF453A",
    }).setData(candles.map(c => ({ time: c.date as string, open: c.open, high: c.high, low: c.low, close: c.close })));

    // Volume
    const vol = mc.addSeries(HistogramSeries, { priceScaleId: "vol", priceFormat: { type: "volume" } });
    mc.priceScale("vol").applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } });
    vol.setData(candles.map(c => ({
      time: c.date as string, value: c.volume,
      color: c.close >= c.open ? "rgba(50,215,75,0.15)" : "rgba(255,69,58,0.15)",
    })));

    // Bollinger Bands
    if (showBollinger && chartData.indicators?.bollinger) {
      const [upper, sma, lower] = chartData.indicators.bollinger;
      mc.addSeries(LineSeries, {
        color: "rgba(86,211,255,0.5)", lineWidth: 1, priceScaleId: "right",
        lastValueVisible: false, priceLineVisible: false,
      }).setData(candles.map((c, i) => ({ time: c.date as string, value: typeof upper[i] === "number" ? upper[i] as number : NaN })).filter(p => !isNaN(p.value)));
      mc.addSeries(LineSeries, {
        color: "rgba(252,213,53,0.6)", lineWidth: 1, lineStyle: 2, priceScaleId: "right",
        lastValueVisible: false, priceLineVisible: false,
      }).setData(candles.map((c, i) => ({ time: c.date as string, value: typeof sma[i] === "number" ? sma[i] as number : NaN })).filter(p => !isNaN(p.value)));
      mc.addSeries(LineSeries, {
        color: "rgba(86,211,255,0.5)", lineWidth: 1, priceScaleId: "right",
        lastValueVisible: false, priceLineVisible: false,
      }).setData(candles.map((c, i) => ({ time: c.date as string, value: typeof lower[i] === "number" ? lower[i] as number : NaN })).filter(p => !isNaN(p.value)));
    }

    // SMA 9 + 20
    if (showMA) {
      const closes = candles.map(c => c.close);
      const ma9 = calcSMA(closes, 9);
      const ma20 = calcSMA(closes, 20);
      mc.addSeries(LineSeries, { color: "#FF9500", lineWidth: 1, priceScaleId: "right", lastValueVisible: false, priceLineVisible: false })
        .setData(candles.map((c, i) => ({ time: c.date as string, value: ma9[i] ?? NaN })).filter(p => !isNaN(p.value)));
      mc.addSeries(LineSeries, { color: "#AF52DE", lineWidth: 1, priceScaleId: "right", lastValueVisible: false, priceLineVisible: false })
        .setData(candles.map((c, i) => ({ time: c.date as string, value: ma20[i] ?? NaN })).filter(p => !isNaN(p.value)));
    }

    // EMA 50 + 200
    if (showEMA) {
      const closes = candles.map(c => c.close);
      const ema50 = calcEMA(closes, 50);
      const ema200 = calcEMA(closes, 200);
      mc.addSeries(LineSeries, { color: "#20D6A1", lineWidth: 2, priceScaleId: "right", lastValueVisible: false, priceLineVisible: false })
        .setData(candles.map((c, i) => ({ time: c.date as string, value: ema50[i] ?? NaN })).filter(p => !isNaN(p.value)));
      if (closes.length >= 200) {
        mc.addSeries(LineSeries, { color: "#FF6B6B", lineWidth: 2, priceScaleId: "right", lastValueVisible: false, priceLineVisible: false })
          .setData(candles.map((c, i) => ({ time: c.date as string, value: ema200[i] ?? NaN })).filter(p => !isNaN(p.value)));
      }
    }

    // VWAP (approximation: cumulative typical price * volume / cumulative volume)
    if (showVWAP) {
      let cumTPV = 0;
      let cumVol = 0;
      const vwapData = candles.map((c) => {
        const tp = (c.high + c.low + c.close) / 3;
        cumTPV += tp * c.volume;
        cumVol += c.volume;
        return { time: c.date as string, value: cumVol > 0 ? cumTPV / cumVol : NaN };
      }).filter(p => !isNaN(p.value));
      mc.addSeries(LineSeries, { color: "#FCD535", lineWidth: 2, lineStyle: 2, priceScaleId: "right", lastValueVisible: false, priceLineVisible: false })
        .setData(vwapData);
    }

    // Show all data without empty space — fitContent ensures data fills the view
    // Use scrollToPosition to ensure chart starts from data, not empty space
    const totalBars = candles.length;
    if (totalBars > 0) {
      mc.timeScale().fitContent();
      // Slight offset so latest bar isn't stuck to the right edge
      mc.timeScale().scrollToPosition(5, false);
    }

    // RSI
    if (showRsi && chartData.indicators?.rsi && rsiRef.current) {
      const rc = createChart(rsiRef.current, { ...CHART_OPTS, timeScale: { visible: false, rightOffset: 5 }, height: 150 });
      rsiChart.current = rc;
      const rsiData = chartData.indicators.rsi;
      rc.addSeries(LineSeries, { color: "#FF9500", lineWidth: 2, priceFormat: { type: "custom", formatter: (v: number) => v.toFixed(0) } })
        .setData(candles.map((c, i) => ({ time: c.date as string, value: typeof rsiData[i] === "number" ? rsiData[i] as number : NaN })).filter(p => !isNaN(p.value)));

      // Overbought/oversold lines
      rc.addSeries(LineSeries, { color: "rgba(255,69,58,0.3)", lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false })
        .setData(candles.map(c => ({ time: c.date as string, value: 70 })));
      rc.addSeries(LineSeries, { color: "rgba(50,215,75,0.3)", lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false })
        .setData(candles.map(c => ({ time: c.date as string, value: 30 })));

      mc.timeScale().subscribeVisibleLogicalRangeChange(r => { if (r) rc.timeScale().setVisibleLogicalRange(r); });
      rc.timeScale().subscribeVisibleLogicalRangeChange(r => { if (r) mc.timeScale().setVisibleLogicalRange(r); });
    }

    // MACD
    if (showMacd && chartData.indicators?.macd && macdRef.current) {
      const md = createChart(macdRef.current, { ...CHART_OPTS, timeScale: { visible: false, rightOffset: 5 }, height: 150 });
      macdChart.current = md;
      const { macd, signal, histogram } = chartData.indicators.macd;
      md.addSeries(HistogramSeries, {}).setData(
        candles.map((c, i) => ({ time: c.date as string, value: typeof histogram[i] === "number" ? histogram[i] as number : NaN, color: typeof histogram[i] === "number" && (histogram[i] as number) >= 0 ? "rgba(50,215,75,0.5)" : "rgba(255,69,58,0.5)" })).filter(p => !isNaN(p.value))
      );
      md.addSeries(LineSeries, { color: "#AF52DE", lineWidth: 2 }).setData(
        candles.map((c, i) => ({ time: c.date as string, value: typeof macd[i] === "number" ? macd[i] as number : NaN })).filter(p => !isNaN(p.value))
      );
      md.addSeries(LineSeries, { color: "#FF9500", lineWidth: 1 }).setData(
        candles.map((c, i) => ({ time: c.date as string, value: typeof signal[i] === "number" ? signal[i] as number : NaN })).filter(p => !isNaN(p.value))
      );
      mc.timeScale().subscribeVisibleLogicalRangeChange(r => { if (r) md.timeScale().setVisibleLogicalRange(r); });
    }

    return () => {
      mainChart.current?.remove(); mainChart.current = null;
      rsiChart.current?.remove(); rsiChart.current = null;
      macdChart.current?.remove(); macdChart.current = null;
    };
  }, [chartData, showRsi, showMacd, showBollinger, showMA, showEMA, showVWAP]);

  // Resize
  useEffect(() => {
    const onResize = () => {
      const infoW = showInfo ? 240 : 0;
      if (mainRef.current && mainChart.current) mainChart.current.applyOptions({ width: mainRef.current.clientWidth });
      if (rsiRef.current && rsiChart.current) rsiChart.current.applyOptions({ width: rsiRef.current.clientWidth });
      if (macdRef.current && macdChart.current) macdChart.current.applyOptions({ width: macdRef.current.clientWidth });
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [showInfo]);

  const [windowH, setWindowH] = useState(typeof window !== "undefined" ? window.innerHeight : 800);
  useEffect(() => {
    const onH = () => setWindowH(window.innerHeight);
    window.addEventListener("resize", onH);
    return () => window.removeEventListener("resize", onH);
  }, []);

  if (!open) return null;
  const up = priceChange >= 0;
  const subChartsH = (showRsi ? 170 : 0) + (showMacd ? 170 : 0);
  const mainH = Math.max(300, windowH - 128 - subChartsH);

  // Compute stats from candle data
  const lastCandle = chartData?.candles?.[chartData.candles.length - 1];
  const prevCandle = chartData?.candles?.[chartData.candles.length - 2];
  const allCloses = chartData?.candles?.map(c => c.close) || [];
  const high52w = allCloses.length ? Math.max(...allCloses) : 0;
  const low52w = allCloses.length ? Math.min(...allCloses) : 0;
  const avgVol = chartData?.candles?.length ? chartData.candles.reduce((s, c) => s + c.volume, 0) / chartData.candles.length : 0;

  return (
    <div className="fixed inset-0 z-[100] bg-[#0D1117]" onClick={onClose}>
      <div className="w-full h-full flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-white/8">
          <div className="flex items-center gap-4">
            <img src={logoUrl(ticker)} alt="" className="w-8 h-8 rounded-full border border-white/10 bg-[#0B0E14]" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
            <h2 className="text-xl font-black text-white tracking-wider">{ticker}</h2>
            {currentPrice !== null && (
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-white">${currentPrice.toFixed(2)}</span>
                <span className="text-sm font-bold px-2 py-0.5 rounded-lg" style={{ color: up ? "#32D74B" : "#FF453A", background: up ? "rgba(50,215,75,0.1)" : "rgba(255,69,58,0.1)" }}>
                  {up ? "+" : ""}{priceChange.toFixed(2)}%
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowInfo(!showInfo)}
              className={`p-1.5 rounded-lg text-xs font-bold transition-colors ${showInfo ? "bg-[#39C8FF] text-black" : "text-gray-400 hover:text-white hover:bg-white/5"}`}>
              <Info size={16} />
            </button>
            <button onClick={onClose} className="text-gray-500 hover:text-white p-1.5 hover:bg-white/5 rounded-lg transition-colors"><X size={20} /></button>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-2 px-5 py-2.5 border-b border-white/5">
          <div className="flex gap-1">
            {PERIODS.map(p => (
              <button key={p.value} onClick={() => setPeriod(p.value)}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-colors ${period === p.value ? "bg-[#D0FD3E] text-[#080B10]" : "text-gray-400 hover:text-white hover:bg-white/5"}`}>
                {p.label}
              </button>
            ))}
          </div>

          <div className="w-px h-5 bg-white/10 mx-1" />

          {/* Indicator toggles */}
          <button onClick={() => setShowMA(v => !v)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold transition-colors ${showMA ? "bg-[#FF9500] text-black" : "text-gray-400 hover:text-white hover:bg-white/5"}`}>
            <TrendingUp size={12} /> SMA
          </button>
          <button onClick={() => setShowEMA(v => !v)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold transition-colors ${showEMA ? "bg-[#20D6A1] text-black" : "text-gray-400 hover:text-white hover:bg-white/5"}`}>
            <TrendingUp size={12} /> EMA
          </button>
          <button onClick={() => setShowBollinger(v => !v)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold transition-colors ${showBollinger ? "bg-[#56D3FF] text-black" : "text-gray-400 hover:text-white hover:bg-white/5"}`}>
            <Waves size={12} /> BB
          </button>
          <button onClick={() => setShowVWAP(v => !v)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold transition-colors ${showVWAP ? "bg-[#FCD535] text-black" : "text-gray-400 hover:text-white hover:bg-white/5"}`}>
            VWAP
          </button>
          <button onClick={() => setShowRsi(v => !v)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold transition-colors ${showRsi ? "bg-[#FF9500] text-black" : "text-gray-400 hover:text-white hover:bg-white/5"}`}>
            <Activity size={12} /> RSI
          </button>
          <button onClick={() => setShowMacd(v => !v)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold transition-colors ${showMacd ? "bg-[#AF52DE] text-white" : "text-gray-400 hover:text-white hover:bg-white/5"}`}>
            <BarChart3 size={12} /> MACD
          </button>

          {/* Legend */}
          {(showMA || showBollinger || showEMA || showVWAP) && (
            <>
              <div className="w-px h-5 bg-white/10 mx-1" />
              <div className="flex items-center gap-3 text-[10px] font-bold text-gray-500">
                {showMA && (
                  <>
                    <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#FF9500] rounded" />SMA9</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#AF52DE] rounded" />SMA20</span>
                  </>
                )}
                {showEMA && (
                  <>
                    <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#20D6A1] rounded" />EMA50</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#FF6B6B] rounded" />EMA200</span>
                  </>
                )}
                {showBollinger && (
                  <>
                    <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#56D3FF] rounded" />BB</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#FCD535] rounded" style={{ opacity: 0.6 }} />SMA20</span>
                  </>
                )}
                {showVWAP && (
                  <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#FCD535] rounded" style={{ borderStyle: 'dashed' }} />VWAP</span>
                )}
              </div>
            </>
          )}
        </div>

        {/* Main area with optional left info panel */}
        <div className="flex-1 flex overflow-hidden min-h-0">
          {/* Left Info Panel */}
          {showInfo && (
            <div className="w-[240px] shrink-0 border-r border-white/8 overflow-y-auto p-4 space-y-4">
              <div>
                <span className="text-[9px] font-black text-gray-500 tracking-widest uppercase">PRICE DATA</span>
                {lastCandle && (
                  <div className="mt-2 space-y-1.5">
                    {[
                      { label: "Open", value: lastCandle.open },
                      { label: "High", value: lastCandle.high },
                      { label: "Low", value: lastCandle.low },
                      { label: "Close", value: lastCandle.close },
                    ].map(row => (
                      <div key={row.label} className="flex justify-between text-xs">
                        <span className="text-gray-500">{row.label}</span>
                        <span className="text-white font-bold tabular-nums">${row.value.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="w-full h-px bg-white/8" />

              <div>
                <span className="text-[9px] font-black text-gray-500 tracking-widest uppercase">VOLUME</span>
                <div className="mt-2 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Last</span>
                    <span className="text-white font-bold tabular-nums">
                      {lastCandle ? (lastCandle.volume >= 1e6 ? (lastCandle.volume / 1e6).toFixed(1) + "M" : (lastCandle.volume / 1e3).toFixed(0) + "K") : "—"}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Avg</span>
                    <span className="text-white font-bold tabular-nums">
                      {avgVol >= 1e6 ? (avgVol / 1e6).toFixed(1) + "M" : (avgVol / 1e3).toFixed(0) + "K"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="w-full h-px bg-white/8" />

              <div>
                <span className="text-[9px] font-black text-gray-500 tracking-widest uppercase">RANGE ({period.toUpperCase()})</span>
                <div className="mt-2 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">High</span>
                    <span className="text-[#32D74B] font-bold tabular-nums">${high52w.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Low</span>
                    <span className="text-[#FF453A] font-bold tabular-nums">${low52w.toFixed(2)}</span>
                  </div>
                  {currentPrice && high52w > low52w && (
                    <div className="mt-1">
                      <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-[#D0FD3E]"
                          style={{ width: `${Math.min(100, Math.max(2, ((currentPrice - low52w) / (high52w - low52w)) * 100))}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="w-full h-px bg-white/8" />

              <div>
                <span className="text-[9px] font-black text-gray-500 tracking-widest uppercase">CHANGE</span>
                <div className="mt-2 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Period</span>
                    <span className="font-bold tabular-nums" style={{ color: up ? "#32D74B" : "#FF453A" }}>
                      {up ? "+" : ""}{priceChange.toFixed(2)}%
                    </span>
                  </div>
                  {prevCandle && lastCandle && (
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-500">Daily</span>
                      <span className="font-bold tabular-nums" style={{ color: lastCandle.close >= prevCandle.close ? "#32D74B" : "#FF453A" }}>
                        {lastCandle.close >= prevCandle.close ? "+" : ""}
                        {((lastCandle.close - prevCandle.close) / prevCandle.close * 100).toFixed(2)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Candle count */}
              <div className="w-full h-px bg-white/8" />
              <div className="text-[10px] text-gray-600 text-center">
                {chartData?.candles?.length || 0} candles · {period.toUpperCase()}
              </div>
            </div>
          )}

          {/* Chart area */}
          <div className="flex-1 overflow-y-auto px-2 py-2 relative min-h-0">
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center z-10 bg-[#0D1117]/80">
                <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
              </div>
            )}
            <div ref={mainRef} className="w-full" style={{ height: mainH }} />
            {showRsi && (
              <div className="mt-1">
                <span className="text-[10px] text-[#FF9500] font-bold tracking-wider px-1">RSI (14)</span>
                <div ref={rsiRef} className="w-full" style={{ height: 150 }} />
              </div>
            )}
            {showMacd && (
              <div className="mt-1">
                <span className="text-[10px] text-[#AF52DE] font-bold tracking-wider px-1">MACD (12, 26, 9)</span>
                <div ref={macdRef} className="w-full" style={{ height: 150 }} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
