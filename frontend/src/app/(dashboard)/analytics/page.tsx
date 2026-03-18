"use client";

import { useState, useMemo } from "react";
import { useAuth } from "@/lib/auth-store";
import { useLang, tr } from "@/lib/i18n";
import { usePortfolio } from "@/lib/hooks";
import ProGate from "@/components/pro-gate";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import api from "@/lib/api";
import {
  PieChart,
  Loader2,
  BarChart3,
  TrendingUp,
  Shield,
  ArrowUpRight,
  ArrowDownRight,
  HeartPulse,
  Stethoscope,
} from "lucide-react";

const COLORS = [
  "#D0FD3E", "#39C8FF", "#FF9500", "#AF52DE", "#32D74B",
  "#FF453A", "#FCD535", "#00C853", "#FF2D55", "#5AC8FA",
  "#FF6B35", "#64D2FF", "#BF5AF2", "#30D158",
];

function fmt(n: number) {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

type Mode = "allocation" | "performance" | "groups" | "port-doctor";

export default function AnalyticsPage() {
  const user = useAuth((s) => s.user);
  const { lang } = useLang();
  const { items, summary, loading } = usePortfolio();
  const [mode, setMode] = useState<Mode>("allocation");
  const [doctorLoading, setDoctorLoading] = useState(false);
  const [doctorResult, setDoctorResult] = useState<string | null>(null);

  const role = user?.role?.toLowerCase() || "free";
  const isPro = ["pro", "admin"].includes(role);

  // Allocation data
  const allocationData = useMemo(() => {
    if (!items.length) return [];
    const total = items.reduce((sum, i) => sum + i.value, 0);
    return items
      .map((item, idx) => ({
        ticker: item.ticker,
        value: item.value,
        pct: total > 0 ? (item.value / total) * 100 : 0,
        color: COLORS[idx % COLORS.length],
      }))
      .sort((a, b) => b.value - a.value);
  }, [items]);

  // Group data
  const groupData = useMemo(() => {
    if (!items.length) return [];
    const groups: Record<string, { value: number; cost: number; count: number }> = {};
    for (const item of items) {
      const g = item.asset_group || "ALL";
      if (!groups[g]) groups[g] = { value: 0, cost: 0, count: 0 };
      groups[g].value += item.value;
      groups[g].cost += item.cost;
      groups[g].count += 1;
    }
    const total = items.reduce((s, i) => s + i.value, 0);
    return Object.entries(groups)
      .map(([name, data], idx) => ({
        name,
        ...data,
        pnl: data.value - data.cost,
        pnlPct: data.cost > 0 ? ((data.value - data.cost) / data.cost) * 100 : 0,
        pct: total > 0 ? (data.value / total) * 100 : 0,
        color: COLORS[idx % COLORS.length],
      }))
      .sort((a, b) => b.value - a.value);
  }, [items]);

  // Performance data
  const performanceData = useMemo(() => {
    return [...items]
      .map((item, idx) => ({
        ticker: item.ticker,
        pnl: item.pnl,
        pnlPct: item.pnl_pct,
        value: item.value,
        color: COLORS[idx % COLORS.length],
      }))
      .sort((a, b) => b.pnlPct - a.pnlPct);
  }, [items]);

  // Simple SVG pie chart
  const PieChartSVG = ({ data }: { data: { pct: number; color: string; ticker?: string; name?: string }[] }) => {
    let cumulative = 0;
    const size = 200;
    const center = size / 2;
    const radius = 80;

    return (
      <svg viewBox={`0 0 ${size} ${size}`} className="w-48 h-48 mx-auto">
        {data.map((slice, i) => {
          const startAngle = (cumulative / 100) * 360 - 90;
          cumulative += slice.pct;
          const endAngle = (cumulative / 100) * 360 - 90;
          const largeArc = slice.pct > 50 ? 1 : 0;
          const x1 = center + radius * Math.cos((startAngle * Math.PI) / 180);
          const y1 = center + radius * Math.sin((startAngle * Math.PI) / 180);
          const x2 = center + radius * Math.cos((endAngle * Math.PI) / 180);
          const y2 = center + radius * Math.sin((endAngle * Math.PI) / 180);
          if (slice.pct < 0.5) return null;
          return (
            <path key={i}
              d={`M ${center} ${center} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`}
              fill={slice.color} stroke="#0D1117" strokeWidth="2" opacity={0.85} />
          );
        })}
        <circle cx={center} cy={center} r={40} fill="#0D1117" />
        <text x={center} y={center - 5} textAnchor="middle" fill="white" fontSize="14" fontWeight="900">
          {data.length}
        </text>
        <text x={center} y={center + 12} textAnchor="middle" fill="#8B949E" fontSize="9">
          {mode === "groups" ? "groups" : "stocks"}
        </text>
      </svg>
    );
  };

  // Port Doctor scan
  const runPortDoctor = async () => {
    if (!isPro) return;
    setDoctorLoading(true);
    setDoctorResult(null);
    try {
      const portStr = items.map(i => `${i.ticker}: $${i.value.toFixed(0)}`).join(", ");
      const { data } = await api.post("/api/ai/port-doctor", { portfolio: portStr });
      setDoctorResult(data.diagnosis || data.result || "No diagnosis available");
    } catch {
      setDoctorResult(lang === "TH"
        ? "ไม่สามารถเชื่อมต่อ AI ได้ในขณะนี้ กรุณาลองใหม่"
        : "Unable to connect to AI service. Please try again.");
    } finally {
      setDoctorLoading(false);
    }
  };

  const modes: { key: Mode; label: string; icon: typeof PieChart }[] = [
    { key: "allocation", label: "Allocation", icon: PieChart },
    { key: "performance", label: "Performance", icon: TrendingUp },
    { key: "groups", label: "Groups", icon: Shield },
    { key: "port-doctor", label: "Port Doctor", icon: Stethoscope },
  ];

  return (
    <ProGate>
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-black text-white tracking-wide flex items-center gap-3">
            <BarChart3 className="text-[#AF52DE]" size={24} />
            {lang === "TH" ? "วิเคราะห์พอร์ตเชิงลึก" : "Portfolio Analytics"}
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            {lang === "TH"
              ? "เจาะลึกประสิทธิภาพพอร์ตและกลยุทธ์ AI"
              : "Deep dive into your portfolio performance and AI strategy"}
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
          </div>
        ) : items.length === 0 ? (
          <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-12 text-center">
            <PieChart className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h2 className="text-lg font-bold text-white mb-2">No data yet</h2>
            <p className="text-gray-500 text-sm">Add stocks to your portfolio to see analytics</p>
          </div>
        ) : (
          <>
            {/* Mode toggle */}
            <div className="flex gap-2 mb-6 flex-wrap">
              {modes.map((m) => (
                <button key={m.key} onClick={() => setMode(m.key)}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-bold transition-colors ${
                    mode === m.key
                      ? m.key === "port-doctor"
                        ? "bg-[#32D74B] text-black"
                        : "bg-[#D0FD3E] text-[#080B10]"
                      : "text-gray-400 bg-white/5 border border-white/10 hover:text-white hover:bg-white/10"
                  }`}>
                  <m.icon size={14} />
                  {m.label}
                </button>
              ))}
            </div>

            {/* Port Doctor mode */}
            {mode === "port-doctor" ? (
              <div className="bg-gradient-to-br from-[#12161E] to-[#0B0E14] border border-[#32D74B]/20 rounded-[28px] p-8 md:p-12 relative overflow-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(50,215,75,0.08),transparent)] pointer-events-none" />

                <div className="relative z-10 flex flex-col items-center text-center">
                  <HeartPulse size={64} className="text-[#32D74B] mb-4 drop-shadow-[0_0_20px_rgba(50,215,75,0.8)] animate-pulse" />
                  <h2 className="text-2xl md:text-3xl font-black text-white tracking-widest">
                    {lang === "TH" ? "PORT DOCTOR วินิจฉัย" : "PORT DOCTOR DIAGNOSIS"}
                  </h2>
                  <p className="text-gray-400 text-sm mt-2 max-w-md">
                    {lang === "TH"
                      ? "AI สแกนสุขภาพพอร์ตเชิงลึกและแนะนำวิธีแก้ไข"
                      : "AI scans your portfolio health deeply and suggests practical fixes"}
                  </p>

                  {!doctorResult && !doctorLoading && (
                    isPro ? (
                      <button onClick={runPortDoctor}
                        className="mt-8 flex items-center gap-2 bg-[#1C2128] border border-[#32D74B]/50 text-[#32D74B] font-black py-4 px-10 rounded-full shadow-[0_0_30px_rgba(50,215,75,0.2)] hover:bg-[#32D74B] hover:text-black transition-all text-lg">
                        <Stethoscope size={20} />
                        {lang === "TH" ? "เริ่มสแกนพอร์ต" : "Start Portfolio Scan"}
                      </button>
                    ) : (
                      <div className="mt-8 flex flex-col items-center gap-3">
                        <p className="text-sm text-[#FCD535] font-bold">
                          {lang === "TH" ? "สงวนสิทธิ์สำหรับ PRO เท่านั้น" : "PRO members only"}
                        </p>
                        <button onClick={() => window.open("/payment", "_self")}
                          className="flex items-center gap-2 bg-[#FCD535] text-black font-black py-3 px-8 rounded-full hover:scale-105 transition-transform">
                          {lang === "TH" ? "อัปเกรดเป็น PRO" : "UPGRADE TO PRO"}
                        </button>
                      </div>
                    )
                  )}

                  {doctorLoading && (
                    <div className="mt-8 flex items-center gap-3">
                      <Loader2 size={24} className="animate-spin text-[#32D74B]" />
                      <span className="text-gray-400 font-bold">
                        {lang === "TH" ? "กำลังวิเคราะห์..." : "Analyzing..."}
                      </span>
                    </div>
                  )}

                  {doctorResult && (
                    <div className="mt-6 w-full max-w-2xl text-left bg-[#0B0E14]/80 backdrop-blur-md p-6 md:p-8 rounded-[24px] border border-[#32D74B]/30 shadow-[0_0_30px_rgba(50,215,75,0.1)]">
                      <Markdown remarkPlugins={[remarkGfm]} components={{
                        h2: ({ children }) => (
                          <h2 className="text-lg font-black text-white mt-6 mb-3 tracking-wide flex items-center gap-2 border-b border-[#32D74B]/20 pb-2">
                            {children}
                          </h2>
                        ),
                        h3: ({ children }) => <h3 className="text-base font-bold text-gray-200 mt-4 mb-2">{children}</h3>,
                        p: ({ children }) => <p className="text-gray-300 leading-relaxed text-sm my-2 bg-white/[0.02] rounded-lg px-3 py-2">{children}</p>,
                        ul: ({ children }) => <ul className="space-y-1.5 my-2">{children}</ul>,
                        li: ({ children }) => <li className="text-gray-300 text-sm flex items-start gap-1.5"><span className="text-[#32D74B] mt-0.5">▸</span><span>{children}</span></li>,
                        strong: ({ children }) => <strong className="text-[#D0FD3E] font-black">{children}</strong>,
                        em: ({ children }) => <em className="text-[#39C8FF] not-italic font-semibold">{children}</em>,
                        table: ({ children }) => (
                          <div className="overflow-x-auto mt-3 mb-4 rounded-2xl border border-[#32D74B]/20 shadow-[0_0_20px_rgba(50,215,75,0.05)]">
                            <table className="w-full border-collapse" style={{ background: "rgba(13,17,23,0.6)" }}>{children}</table>
                          </div>
                        ),
                        thead: ({ children }) => <thead className="bg-gradient-to-r from-[#32D74B]/15 to-[#32D74B]/5">{children}</thead>,
                        th: ({ children }) => <th className="px-4 py-3.5 text-[11px] font-black text-[#32D74B] tracking-wider text-left border-b border-[#32D74B]/30 whitespace-nowrap">{children}</th>,
                        td: ({ children }) => <td className="px-4 py-3.5 text-sm text-gray-200 border-b border-white/5 whitespace-nowrap">{children}</td>,
                        tr: ({ children }) => <tr className="hover:bg-[#32D74B]/[0.04] transition-colors">{children}</tr>,
                      }}>{doctorResult}</Markdown>
                      <button onClick={runPortDoctor}
                        className="mt-4 text-sm text-[#32D74B] font-bold hover:underline">
                        {lang === "TH" ? "สแกนอีกครั้ง" : "Scan Again"}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <>
                {/* Summary cards */}
                {summary && (
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-4">
                      <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Total Value</span>
                      <p className="text-xl font-black text-white tabular-nums mt-1">${fmt(summary.total_value)}</p>
                    </div>
                    <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-4">
                      <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Total Cost</span>
                      <p className="text-xl font-black text-gray-400 tabular-nums mt-1">${fmt(summary.total_cost)}</p>
                    </div>
                    <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-4">
                      <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Total P&L</span>
                      <p className="text-xl font-black tabular-nums mt-1"
                        style={{ color: summary.total_pnl >= 0 ? "#32D74B" : "#FF453A" }}>
                        {summary.total_pnl >= 0 ? "+" : ""}${fmt(summary.total_pnl)}
                      </p>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Pie Chart */}
                  <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-6">
                    <PieChartSVG
                      data={mode === "groups"
                        ? groupData.map((g) => ({ pct: g.pct, color: g.color, name: g.name }))
                        : allocationData.map((a) => ({ pct: a.pct, color: a.color, ticker: a.ticker }))
                      }
                    />
                  </div>

                  {/* Data list */}
                  <div className="lg:col-span-2 bg-[#0D1117] border border-white/8 rounded-2xl overflow-hidden">
                    {mode === "allocation" && (
                      <div className="divide-y divide-white/5">
                        {allocationData.map((item) => (
                          <div key={item.ticker} className="flex items-center justify-between px-5 py-3 hover:bg-white/[0.02]">
                            <div className="flex items-center gap-3">
                              <div className="w-3 h-3 rounded-full" style={{ background: item.color }} />
                              <span className="font-bold text-white">{item.ticker}</span>
                            </div>
                            <div className="text-right">
                              <span className="text-white font-mono text-sm tabular-nums">${fmt(item.value)}</span>
                              <span className="block text-[10px] text-gray-500 font-bold">{item.pct.toFixed(1)}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {mode === "performance" && (
                      <div className="divide-y divide-white/5">
                        {performanceData.map((item) => {
                          const up = item.pnlPct >= 0;
                          return (
                            <div key={item.ticker} className="flex items-center justify-between px-5 py-3 hover:bg-white/[0.02]">
                              <div className="flex items-center gap-3">
                                <div className="w-3 h-3 rounded-full" style={{ background: item.color }} />
                                <span className="font-bold text-white">{item.ticker}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                {up ? <ArrowUpRight size={14} className="text-[#32D74B]" /> : <ArrowDownRight size={14} className="text-[#FF453A]" />}
                                <div className="text-right">
                                  <span className="font-mono text-sm font-bold tabular-nums"
                                    style={{ color: up ? "#32D74B" : "#FF453A" }}>
                                    {up ? "+" : ""}{fmt(item.pnl)}
                                  </span>
                                  <span className="block text-[10px] font-bold tabular-nums"
                                    style={{ color: up ? "#32D74B" : "#FF453A" }}>
                                    {up ? "+" : ""}{item.pnlPct.toFixed(2)}%
                                  </span>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {mode === "groups" && (
                      <div className="divide-y divide-white/5">
                        {groupData.map((group) => {
                          const up = group.pnl >= 0;
                          return (
                            <div key={group.name} className="flex items-center justify-between px-5 py-3 hover:bg-white/[0.02]">
                              <div className="flex items-center gap-3">
                                <div className="w-3 h-3 rounded-full" style={{ background: group.color }} />
                                <div>
                                  <span className="font-bold text-white">{group.name}</span>
                                  <span className="block text-[10px] text-gray-500">{group.count} stock{group.count !== 1 && "s"}</span>
                                </div>
                              </div>
                              <div className="text-right">
                                <span className="text-white font-mono text-sm tabular-nums">${fmt(group.value)}</span>
                                <span className="block text-[10px] font-bold tabular-nums"
                                  style={{ color: up ? "#32D74B" : "#FF453A" }}>
                                  {up ? "+" : ""}{group.pnlPct.toFixed(2)}%
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </ProGate>
  );
}
