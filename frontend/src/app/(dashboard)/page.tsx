"use client";

import { useState, useMemo } from "react";
import { useAuth } from "@/lib/auth-store";
import { useLang, tr } from "@/lib/i18n";
import { usePortfolio, useAlerts, useMacro } from "@/lib/hooks";
import Sparkline from "@/components/sparkline";
import AddStockModal from "@/components/add-stock-modal";
import EditStockModal from "@/components/edit-stock-modal";
import ChartModal from "@/components/chart-modal";
import TradePlanPanel from "@/components/trade-plan";
import HealthScorePanel from "@/components/health-score";
import PerformanceAttribution from "@/components/performance-attribution";
import RebalanceModal from "@/components/rebalance-modal";
import AnimatedNumber from "@/components/animated-number";
import api from "@/lib/api";
import { fmt, fmtPct, logoUrl, computeHealthScore } from "@/lib/dashboard-helpers";
import {
  TrendingUp,
  TrendingDown,
  Rocket,
  Plus,
  Trash2,
  Pencil,
  RefreshCw,
  Loader2,
  MessageSquare,
  Zap,
  User,
  CandlestickChart,
  Activity,
  Crown,
  Brain,
} from "lucide-react";

type SortMode = "az" | "profit" | "value";
type GroupFilter = "ALL" | "DCA" | "DIV" | "TRADING";

export default function DashboardPage() {
  const user = useAuth((s) => s.user);
  const { lang } = useLang();
  const [displayCurrency, setDisplayCurrency] = useState<"USD" | "THB">("USD");
  const { items: rawItems, summary: rawSummary, loading, error, refresh } = usePortfolio("USD", 30000);

  // Client-side currency conversion — instant, no API call
  const thbRate = rawSummary?.thb_rate || 34;
  const rate = displayCurrency === "THB" ? thbRate : 1;
  const items = useMemo(() => rawItems.map(i => ({
    ...i,
    price: i.price * rate,
    value: i.value * rate,
    cost: i.cost * rate,
    avg_cost: i.avg_cost * rate,
    pnl: i.pnl * rate,
  })), [rawItems, rate]);
  const summary = useMemo(() => rawSummary ? {
    ...rawSummary,
    total_value: rawSummary.total_value * rate,
    total_cost: rawSummary.total_cost * rate,
    total_pnl: rawSummary.total_pnl * rate,
    currency: displayCurrency,
  } : null, [rawSummary, rate, displayCurrency]);
  const currency = displayCurrency;
  const { alerts } = useAlerts();
  const { data: macroData } = useMacro();
  const [showAdd, setShowAdd] = useState(false);
  const [chartTicker, setChartTicker] = useState<string | null>(null);
  const [editStock, setEditStock] = useState<(typeof items)[0] | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [sortMode, setSortMode] = useState<SortMode>("az");
  const [groupFilter, setGroupFilter] = useState<GroupFilter>("ALL");
  const [rebalanceOpen, setRebalanceOpen] = useState(false);
  const [rebalanceLoading, setRebalanceLoading] = useState(false);
  const [rebalanceResult, setRebalanceResult] = useState<string | null>(null);

  const role = (user?.role || "free").toLowerCase();
  const isProPlan = ["pro", "vip", "admin"].includes(role);
  const isProfitOverall = (summary?.total_pnl ?? 0) >= 0;
  const totalPnlPct = summary && summary.total_cost > 0 ? (summary.total_pnl / summary.total_cost) * 100 : 0;
  const currSymbol = currency === "THB" ? "฿" : "$";

  const handleRefresh = async () => {
    setRefreshing(true);
    await refresh();
    setRefreshing(false);
  };

  const handleRebalance = async () => {
    if (!["pro", "admin"].includes(role)) return;
    setRebalanceOpen(true);
    setRebalanceLoading(true);
    setRebalanceResult(null);
    try {
      const total = items.reduce((s, i) => s + Math.max(i.value, 0), 0);
      const portStr = items.map(i => {
        const alloc = total > 0 ? ((i.value / total) * 100).toFixed(2) : "0";
        return `- ${i.ticker}: allocation ${alloc}%, profit ${i.pnl_pct >= 0 ? "+" : ""}${i.pnl_pct.toFixed(2)}%`;
      }).join("\n");
      const { data } = await api.post("/api/ai/rebalance", { portfolio: portStr });
      setRebalanceResult(data.strategy || "No strategy available");
    } catch {
      setRebalanceResult(lang === "TH" ? "ไม่สามารถเชื่อมต่อ AI ได้" : "Unable to connect to AI service");
    } finally {
      setRebalanceLoading(false);
    }
  };

  const handleDelete = async (ticker: string) => {
    if (!confirm(`Remove ${ticker} from portfolio?`)) return;
    setDeleting(ticker);
    try {
      await api.delete(`/api/portfolio/${ticker}`);
      await refresh();
    } catch { /* ignore */ } finally {
      setDeleting(null);
    }
  };

  const sorted = useMemo(() => {
    let filtered = [...items];
    if (groupFilter !== "ALL") {
      filtered = filtered.filter(i => (i.asset_group || "").toUpperCase() === groupFilter);
    }
    switch (sortMode) {
      case "profit": return filtered.sort((a, b) => b.pnl_pct - a.pnl_pct);
      case "value": return filtered.sort((a, b) => b.value - a.value);
      default: return filtered.sort((a, b) => a.ticker.localeCompare(b.ticker));
    }
  }, [items, sortMode, groupFilter]);

  const profitSorted = useMemo(() => [...items].sort((a, b) => b.pnl_pct - a.pnl_pct), [items]);
  const topGainer = profitSorted.length && profitSorted[0].pnl_pct > 0 ? profitSorted[0] : null;
  const topLoser = profitSorted.length && profitSorted[profitSorted.length - 1].pnl_pct < 0 ? profitSorted[profitSorted.length - 1] : null;
  const health = useMemo(() => computeHealthScore(items.map(i => ({ value: i.value, pnl_pct: i.pnl_pct }))), [items]);

  return (
    <div className="max-w-7xl mx-auto space-y-4 md:space-y-6">

      {/* ═══════ ROW 1: Profile Card + Command Center ═══════ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 md:gap-4">
        {/* User Profile Card */}
        <div className="bg-[#12161E]/80 backdrop-blur-xl p-3 md:p-5 rounded-[20px] border border-white/5 shadow-lg hover:border-white/10 transition-all">
          <div className="flex items-center gap-3 mb-3">
            <User size={24} className={role === "free" ? "text-gray-400" : "text-[#D0FD3E]"} />
            <div>
              <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">{tr("dashboard.welcome", lang)}</p>
              <p className="text-lg font-black text-white tracking-wide leading-tight">
                {user?.username || "Trader"}
              </p>
              <span className="inline-block text-[9px] px-2 py-0.5 mt-1 rounded-full border border-[#D0FD3E]/30 bg-[#D0FD3E]/10 text-[#D0FD3E] font-black tracking-widest uppercase">
                {(user?.role || "FREE").toUpperCase()} MEMBER
              </span>
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {[
              `TG: ${user?.telegram_id ? String(user.telegram_id).slice(-6) : "N/A"}`,
              `CUR: ${currency}`,
              `HOLDINGS: ${items.length}`,
              `ALERTS: ${alerts.length}`,
              `EXPOSURE: ${currSymbol}${summary ? summary.total_cost.toLocaleString("en-US", { maximumFractionDigits: 0 }) : "0"}`,
            ].map((chip) => (
              <span key={chip} className="text-[9px] md:text-[10px] font-bold px-2 py-1 rounded-full bg-white/5 text-gray-300 border border-white/10">
                {chip}
              </span>
            ))}
            <span className="text-[9px] md:text-[10px] font-bold px-2 py-1 rounded-full bg-[#20D6A1]/10 text-[#20D6A1] border border-[#20D6A1]/25">
              Ready
            </span>
          </div>
        </div>

        {/* Command Center Card */}
        <div className="bg-gradient-to-br from-[#161B22] to-[#0B0E14] p-3 md:p-5 rounded-[20px] border border-[#20D6A1]/20 shadow-lg relative overflow-hidden hover:border-[#39C8FF]/40 transition-all"
          style={{ boxShadow: "0 0 0 1px rgba(86,211,255,0.1) inset, 0 10px 30px rgba(0,0,0,0.35), 0 0 35px rgba(86,211,255,0.1)" }}
        >
          <p className="text-[10px] text-[#39C8FF] font-black tracking-widest uppercase mb-1">
            {tr("dashboard.command_center", lang)}
          </p>
          <div className="flex items-center gap-1.5 mb-2">
            <Zap size={14} className="text-[#D0FD3E]" />
            <span className="text-xs text-[#D0FD3E]/70 font-bold">Live prices · Auto-refresh 30s</span>
          </div>

          {macroData && (
            <div className="flex items-center gap-4 mb-3">
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-[#FCD535]" />
                <span className="text-[10px] text-gray-500 font-bold">F&G:</span>
                <span className="text-sm font-black" style={{ color: macroData.fear_greed.value <= 25 ? "#FF453A" : macroData.fear_greed.value <= 55 ? "#FCD535" : "#32D74B" }}>
                  {macroData.fear_greed.value}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-[#FF9500]" />
                <span className="text-[10px] text-gray-500 font-bold">VIX:</span>
                <span className="text-sm font-black" style={{ color: macroData.vix < 20 ? "#32D74B" : macroData.vix < 30 ? "#FCD535" : "#FF453A" }}>
                  {macroData.vix.toFixed(2)}
                </span>
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <button onClick={handleRefresh} disabled={refreshing}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-[#20D6A1] text-black font-black rounded-lg text-xs disabled:opacity-50">
              <RefreshCw size={12} className={refreshing ? "animate-spin" : ""} /> Refresh
            </button>
            <button onClick={() => window.open("/payment", "_self")}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-[#39C8FF]/20 text-[#39C8FF] font-black rounded-lg text-xs border border-[#39C8FF]/40">
              <Crown size={12} /> Upgrade
            </button>
          </div>
        </div>
      </div>

      {/* ═══════ ACTION STRIP ═══════ */}
      <div className="flex flex-col md:flex-row justify-between items-center gap-3 bg-[#08141B]/70 backdrop-blur-xl border border-white/8 rounded-[18px] p-3">
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2 bg-[#32D74B]/10 border border-[#32D74B]/30 rounded-full px-4 py-1.5 shadow-inner">
            <TrendingUp size={14} className="text-[#32D74B]" />
            <span className="text-[9px] text-[#32D74B] font-black tracking-widest hidden sm:block">TOP GAINER</span>
            <span className="text-xs md:text-sm font-bold text-white tabular-nums">
              {topGainer ? `${topGainer.ticker} ${fmtPct(topGainer.pnl_pct)}` : "\u2014"}
            </span>
          </div>
          <div className="flex items-center gap-2 bg-[#FF453A]/10 border border-[#FF453A]/30 rounded-full px-4 py-1.5 shadow-inner">
            <TrendingDown size={14} className="text-[#FF453A]" />
            <span className="text-[9px] text-[#FF453A] font-black tracking-widest hidden sm:block">TOP LOSER</span>
            <span className="text-xs md:text-sm font-bold text-white tabular-nums">
              {topLoser ? `${topLoser.ticker} ${fmtPct(topLoser.pnl_pct)}` : "\u2014"}
            </span>
          </div>
        </div>
        <div className="flex gap-2 w-full md:w-auto">
          {["pro", "admin"].includes(role) && items.length > 0 && (
            <button onClick={handleRebalance}
              className="flex-1 md:flex-none flex items-center justify-center gap-1.5 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-500 text-white font-black rounded-full text-sm shadow-[0_0_20px_rgba(147,51,234,0.4)] hover:scale-105 transition-transform">
              <Brain size={14} /> AI Rebalance
            </button>
          )}
          <button onClick={() => setShowAdd(true)}
            className="flex-1 md:flex-none flex items-center justify-center gap-1.5 px-8 py-3 bg-[#D0FD3E] text-black font-black rounded-full text-sm shadow-[0_0_20px_rgba(208,253,62,0.4)] hover:scale-105 transition-transform">
            <Plus size={14} /> {tr("dashboard.add_holding", lang)}
          </button>
        </div>
      </div>

      {/* ═══════ HERO: Portfolio Value Card ═══════ */}
      <div className="relative overflow-hidden bg-gradient-to-br from-[#12161E] to-[#0B0E14] border border-white/5 p-5 md:p-8 rounded-[28px] shadow-[0_10px_40px_rgba(0,0,0,0.5)]"
        style={{ boxShadow: "0 0 0 1px rgba(86,211,255,0.1) inset, 0 10px 30px rgba(0,0,0,0.35), 0 0 35px rgba(86,211,255,0.1)" }}
      >
        <div className="absolute -top-16 -left-10 w-64 h-64 bg-[#20D6A1]/20 rounded-full blur-[70px] pointer-events-none animate-pulse" />
        <div className="absolute -bottom-28 -right-12 w-72 h-72 bg-[#39C8FF]/16 rounded-full blur-[70px] pointer-events-none" />
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-[#D0FD3E]/10 rounded-full blur-[100px] pointer-events-none" />

        <div className="relative z-10">
          <div className="flex justify-between items-center mb-2">
            <p className="text-[10px] md:text-xs text-gray-500 font-black tracking-[0.2em] uppercase">
              {tr("dashboard.total_portfolio_value", lang)}
            </p>
            <div className="flex items-center gap-2">
              <div className="flex bg-white/5 rounded-full border border-white/10 p-0.5">
                {(["USD", "THB"] as const).map(c => (
                  <button key={c} onClick={() => setDisplayCurrency(c)}
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wider transition-all ${currency === c ? "bg-[#D0FD3E] text-black shadow" : "text-gray-500 hover:text-white"}`}>
                    {c}
                  </button>
                ))}
              </div>
              <span className="inline-flex items-center gap-1 text-[10px] text-[#D0FD3E]/60 font-bold">
                <Zap size={10} /> Live
              </span>
            </div>
          </div>

          {loading ? (
            <Loader2 className="w-10 h-10 animate-spin text-[#D0FD3E] my-6" />
          ) : (
            <>
              <AnimatedNumber
                value={summary ? summary.total_value : 0}
                format={fmt}
                prefix={currSymbol}
                duration={800}
                className={`text-4xl md:text-[62px] leading-none font-black text-white tracking-tight drop-shadow-lg ${isProfitOverall ? "animate-pulse-green" : "animate-pulse-red"}`}
              />
              {summary && (
                <p className={`tabular-nums text-base md:text-xl font-black mt-3 drop-shadow-md ${isProfitOverall ? "text-[#32D74B]" : "text-[#FF453A]"}`}>
                  {isProfitOverall ? "+" : "-"}{" "}
                  <AnimatedNumber
                    value={Math.abs(summary.total_pnl)}
                    format={fmt}
                    prefix={currSymbol}
                    duration={800}
                    flash={false}
                  />
                  {" ("}
                  <AnimatedNumber
                    value={totalPnlPct}
                    format={(n) => `${n >= 0 ? "+" : ""}${n.toFixed(2)}`}
                    suffix="%"
                    duration={800}
                    flash={false}
                  />
                  {")"}
                </p>
              )}
            </>
          )}
        </div>
      </div>

      {/* ═══════ PORTFOLIO HOLDINGS ═══════ */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
        </div>
      ) : error ? (
        <div className="text-center py-16 text-[#FF453A]">{error}</div>
      ) : items.length === 0 ? (
        <div className="bg-[#0D1117] border border-dashed border-white/8 rounded-[28px] p-10 md:p-14 text-center relative overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[350px] h-[200px] rounded-full blur-[80px] bg-[#D0FD3E]/5 pointer-events-none" />
          <div className="relative z-10">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5 mx-auto bg-gradient-to-br from-[#D0FD3E]/10 to-[#D0FD3E]/3 border border-[#D0FD3E]/15">
              <Rocket className="w-8 h-8 text-[#D0FD3E]/70" />
            </div>
            <h2 className="text-xl font-black text-gray-300 tracking-wide">No stocks yet</h2>
            <p className="text-sm text-gray-500 mt-1 max-w-md mx-auto">Add stocks via the button above or use the Telegram bot</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center mt-6">
              <button onClick={() => setShowAdd(true)}
                className="inline-flex items-center gap-2 px-6 py-3 bg-[#D0FD3E] text-[#080B10] font-black rounded-xl">
                <Plus size={16} /> Add Your First Stock
              </button>
              <a href="https://t.me/Apexify_Trading_bot" target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white/5 border border-white/10 text-gray-300 font-bold rounded-xl hover:bg-white/10">
                <MessageSquare size={16} /> Open Telegram Bot
              </a>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-3 md:space-y-4">
          {/* Filter + Sort controls */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-[10px] text-gray-500 font-black tracking-widest uppercase pl-1">
              {tr("dashboard.current_portfolio", lang)} · {sorted.length} {tr("dashboard.holdings", lang)}
            </p>
            <div className="flex items-center gap-2">
              <div className="flex bg-white/5 rounded-full border border-white/10 p-0.5">
                {(["ALL", "DCA", "DIV", "TRADING"] as GroupFilter[]).map(g => (
                  <button key={g} onClick={() => setGroupFilter(g)}
                    className={`px-2 py-0.5 rounded-full text-[9px] font-black tracking-wider transition-all ${groupFilter === g ? "bg-[#39C8FF] text-black shadow" : "text-gray-500 hover:text-white"}`}>
                    {g === "ALL" ? tr("dashboard.all", lang) : g}
                  </button>
                ))}
              </div>
              <div className="flex bg-white/5 rounded-full border border-white/10 p-0.5">
                {([
                  { key: "az" as SortMode, label: tr("dashboard.sort.az", lang) },
                  { key: "profit" as SortMode, label: tr("dashboard.sort.profit", lang) },
                  { key: "value" as SortMode, label: tr("dashboard.sort.value", lang) },
                ]).map(s => (
                  <button key={s.key} onClick={() => setSortMode(s.key)}
                    className={`px-2 py-0.5 rounded-full text-[9px] font-black tracking-wider transition-all ${sortMode === s.key ? "bg-[#D0FD3E] text-black shadow" : "text-gray-500 hover:text-white"}`}>
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Stock cards */}
          {sorted.map((s) => {
            const up = s.pnl >= 0;
            const profitColor = up ? "#32D74B" : "#FF453A";
            const isChartUp = s.sparkline?.length > 1 ? s.sparkline[s.sparkline.length - 1] >= s.sparkline[0] : up;

            return (
              <div key={s.ticker}
                className="group flex flex-wrap sm:flex-nowrap items-center justify-between gap-4 bg-[#12161E]/60 hover:bg-[#1C2128]/90 backdrop-blur-xl border border-white/5 hover:border-white/10 rounded-[24px] p-4 md:p-5 transition-all duration-300 hover:-translate-y-1 shadow-lg hover:shadow-2xl cursor-pointer"
              >
                <div className="flex items-center gap-4 shrink-0 min-w-[200px]">
                  <div className="relative">
                    <div className="absolute inset-0 bg-white/10 rounded-full blur-md group-hover:blur-lg transition-all" />
                    <img src={logoUrl(s.ticker)} alt={s.ticker}
                      className="w-12 h-12 md:w-14 md:h-14 rounded-full border-2 border-white/10 relative z-10 bg-[#0B0E14]"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${s.ticker}&background=1a1f26&color=fff&bold=true&size=56`;
                      }}
                    />
                  </div>
                  <div>
                    <p className="text-xl md:text-2xl font-black text-white leading-none tracking-wide">{s.ticker}</p>
                    <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                      <span className="text-[10px] md:text-xs text-gray-300 bg-white/10 px-2 py-0.5 rounded-md font-bold">
                        Price: <AnimatedNumber value={s.price} format={fmt} prefix={currSymbol} duration={500} className="text-[10px] md:text-xs" />
                      </span>
                      <span className="text-[10px] md:text-xs text-gray-400 bg-white/5 px-2 py-0.5 rounded-md">
                        Avg: {currSymbol}{fmt(s.avg_cost)}
                      </span>
                      <span className="text-[10px] md:text-xs text-gray-400 bg-white/5 px-2 py-0.5 rounded-md hidden sm:block">
                        Hold: {s.shares}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex-1 flex items-center justify-center w-full sm:w-auto h-16 min-w-[120px]">
                  <Sparkline data={s.sparkline} width={140} height={50} positive={isChartUp} />
                </div>

                <div className="flex flex-col items-end gap-1 shrink-0 min-w-[160px]">
                  <AnimatedNumber
                    value={s.value}
                    format={fmt}
                    prefix={currSymbol}
                    duration={600}
                    className="text-xl md:text-2xl font-black leading-none tracking-tight drop-shadow-md"
                    style={{ color: profitColor }}
                    positiveColor={profitColor}
                    negativeColor={profitColor}
                  />
                  <span className="tabular-nums text-xs md:text-sm font-bold px-2 py-0.5 rounded-md"
                    style={{ color: profitColor, backgroundColor: `${profitColor}10` }}>
                    <AnimatedNumber
                      value={Math.abs(s.pnl)}
                      format={(n) => `${up ? "+" : ""}${fmt(n)}`}
                      prefix={currSymbol}
                      duration={600}
                      flash={false}
                    />
                    {" ("}
                    <AnimatedNumber value={s.pnl_pct} format={(n) => fmtPct(n)} duration={600} flash={false} />
                    {")"}
                  </span>

                  <div className="flex gap-1 mt-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 md:pointer-events-none md:group-hover:pointer-events-auto transition-opacity duration-300">
                    <button onClick={() => setChartTicker(s.ticker)}
                      className="text-gray-400 hover:text-[#D0FD3E] bg-white/5 p-1.5 rounded-lg transition-colors" title="Chart">
                      <CandlestickChart size={14} />
                    </button>
                    <button onClick={() => setEditStock(s)}
                      className="text-gray-400 hover:text-white bg-white/5 p-1.5 rounded-lg transition-colors" title="Edit">
                      <Pencil size={14} />
                    </button>
                    <button onClick={() => handleDelete(s.ticker)} disabled={deleting === s.ticker}
                      className="text-gray-400 hover:text-[#FF453A] bg-white/5 p-1.5 rounded-lg transition-colors" title="Delete">
                      {deleting === s.ticker ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}

          {summary && (
            <div className="flex flex-wrap justify-between items-center gap-3 text-sm px-2">
              <span className="text-gray-500">
                {items.length} stock{items.length !== 1 && "s"} · Cost: {currSymbol}{fmt(summary.total_cost)}
              </span>
              <span className="font-bold tabular-nums"
                style={{ color: isProfitOverall ? "#32D74B" : "#FF453A" }}>
                Total P&L: <AnimatedNumber value={summary.total_pnl} format={fmt} prefix={currSymbol} duration={600} flash={false} />
                {" ("}<AnimatedNumber value={totalPnlPct} format={(n) => fmtPct(n)} duration={600} flash={false} />{")"}
              </span>
            </div>
          )}
        </div>
      )}

      {/* ═══════ TRADE PLAN ═══════ */}
      <TradePlanPanel items={sorted} isProPlan={isProPlan} currSymbol={currSymbol} lang={lang} onChart={setChartTicker} />

      {/* ═══════ HEALTH SCORE ═══════ */}
      {items.length > 0 && <HealthScorePanel health={health} isProPlan={isProPlan} lang={lang} />}

      {/* ═══════ PERFORMANCE ATTRIBUTION ═══════ */}
      {items.length > 0 && summary && <PerformanceAttribution items={items} summary={summary} currSymbol={currSymbol} />}

      {/* ═══════ MODALS ═══════ */}
      <AddStockModal open={showAdd} onClose={() => setShowAdd(false)} onAdded={refresh} />
      {editStock && (
        <EditStockModal
          ticker={editStock.ticker} shares={editStock.shares} avgCost={editStock.avg_cost}
          alertPrice={editStock.alert_price} assetGroup={editStock.asset_group}
          currentPrice={editStock.price} open={true}
          onClose={() => setEditStock(null)} onSaved={refresh}
        />
      )}
      {chartTicker && <ChartModal ticker={chartTicker} open={true} onClose={() => setChartTicker(null)} />}

      <RebalanceModal
        open={rebalanceOpen} loading={rebalanceLoading} result={rebalanceResult}
        lang={lang} items={items} onClose={() => setRebalanceOpen(false)} onReanalyze={handleRebalance}
      />

      {/* Custom animations */}
      <style jsx>{`
        @keyframes pulse-green-glow {
          0%, 100% { text-shadow: 0 0 0px transparent; }
          50% { text-shadow: 0 0 15px rgba(50,215,75,0.6); }
        }
        @keyframes pulse-red-glow {
          0%, 100% { text-shadow: 0 0 0px transparent; }
          50% { text-shadow: 0 0 15px rgba(255,69,58,0.6); }
        }
        .animate-pulse-green { animation: pulse-green-glow 2s infinite ease-in-out; }
        .animate-pulse-red { animation: pulse-red-glow 2s infinite ease-in-out; }
      `}</style>
    </div>
  );
}
