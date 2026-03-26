"use client";

import { useState, useEffect } from "react";
import { useLang, tr } from "@/lib/i18n";
import { logoUrl } from "@/lib/dashboard-helpers";
import api from "@/lib/api";
import { Calendar, Loader2, Clock, DollarSign } from "lucide-react";
import ProGate from "@/components/pro-gate";

interface Earning {
  ticker: string;
  date: string;
  eps_estimate: number | null;
  revenue_estimate: number | null;
}

function daysUntil(dateStr: string): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(dateStr + "T00:00:00");
  return Math.ceil((target.getTime() - today.getTime()) / 86400000);
}

function dateLabel(dateStr: string, lang: "TH" | "EN"): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString(lang === "TH" ? "th-TH" : "en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function urgencyColor(days: number): string {
  if (days < 0) return "#8B949E";
  if (days <= 3) return "#FF453A";
  if (days <= 7) return "#FF9500";
  if (days <= 14) return "#FCD535";
  return "#32D74B";
}

function fmtRevenue(v: number | null): string {
  if (!v) return "—";
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  return `$${v.toLocaleString()}`;
}

export default function EarningsPage() {
  const { lang } = useLang();
  const [earnings, setEarnings] = useState<Earning[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<{ earnings: Earning[] }>("/api/market/earnings-calendar")
      .then(({ data }) => setEarnings(data.earnings || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const upcoming = earnings.filter((e) => daysUntil(e.date) >= 0);
  const past = earnings.filter((e) => daysUntil(e.date) < 0);

  return (
    <ProGate>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-5">
          <h1
            className="text-2xl font-black tracking-wide flex items-center gap-3"
            style={{ color: "var(--text-primary)" }}
          >
            <Calendar className="text-[#FF9500]" size={24} />
            {lang === "TH" ? "ปฏิทินงบ" : "Earnings Calendar"}
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            {lang === "TH"
              ? "วันประกาศงบของหุ้นในพอร์ตคุณ"
              : "Upcoming earnings dates for your portfolio stocks"}
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
          </div>
        ) : earnings.length === 0 ? (
          <div
            className="border rounded-2xl p-12 text-center"
            style={{
              background: "var(--bg-card)",
              borderColor: "var(--border-default)",
            }}
          >
            <Calendar className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p
              className="text-lg font-bold"
              style={{ color: "var(--text-primary)" }}
            >
              {lang === "TH"
                ? "ไม่พบข้อมูลงบที่กำลังจะมา"
                : "No upcoming earnings found"}
            </p>
            <p className="text-sm mt-2" style={{ color: "var(--text-muted)" }}>
              {lang === "TH"
                ? "เพิ่มหุ้นในพอร์ตเพื่อติดตามวันประกาศงบ"
                : "Add stocks to your portfolio to track earnings"}
            </p>
          </div>
        ) : (
          <>
            {/* Upcoming */}
            {upcoming.length > 0 && (
              <div className="mb-6">
                <p
                  className="text-xs font-black tracking-widest uppercase mb-3 pl-1"
                  style={{ color: "var(--text-muted)" }}
                >
                  {lang === "TH" ? "กำลังจะมา" : "UPCOMING"} ({upcoming.length})
                </p>
                <div className="space-y-2">
                  {upcoming.map((e) => {
                    const days = daysUntil(e.date);
                    const color = urgencyColor(days);
                    return (
                      <div
                        key={e.ticker}
                        className="border rounded-2xl p-4 flex items-center gap-4 hover:brightness-110 transition-all"
                        style={{
                          background: "var(--bg-card)",
                          borderColor: "var(--border-default)",
                        }}
                      >
                        {/* Logo + ticker */}
                        <img
                          src={logoUrl(e.ticker)}
                          alt=""
                          className="w-10 h-10 rounded-full border border-white/10"
                          onError={(ev) => {
                            (ev.target as HTMLImageElement).style.display =
                              "none";
                          }}
                        />
                        <div className="flex-1 min-w-0">
                          <p
                            className="font-black text-base"
                            style={{ color: "var(--text-primary)" }}
                          >
                            {e.ticker}
                          </p>
                          <p
                            className="text-xs"
                            style={{ color: "var(--text-muted)" }}
                          >
                            {dateLabel(e.date, lang)}
                          </p>
                        </div>

                        {/* EPS estimate */}
                        {e.eps_estimate !== null && (
                          <div className="text-center px-3">
                            <p
                              className="text-[10px] uppercase tracking-wider"
                              style={{ color: "var(--text-dim)" }}
                            >
                              EPS Est.
                            </p>
                            <p
                              className="font-black tabular-nums text-sm"
                              style={{ color: "var(--text-primary)" }}
                            >
                              ${e.eps_estimate.toFixed(2)}
                            </p>
                          </div>
                        )}

                        {/* Revenue estimate */}
                        {e.revenue_estimate !== null && (
                          <div className="text-center px-3 hidden sm:block">
                            <p
                              className="text-[10px] uppercase tracking-wider"
                              style={{ color: "var(--text-dim)" }}
                            >
                              Rev Est.
                            </p>
                            <p
                              className="font-black tabular-nums text-sm"
                              style={{ color: "var(--text-primary)" }}
                            >
                              {fmtRevenue(e.revenue_estimate)}
                            </p>
                          </div>
                        )}

                        {/* Countdown badge */}
                        <div
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-black shrink-0"
                          style={{
                            background: `${color}15`,
                            color,
                            border: `1px solid ${color}30`,
                          }}
                        >
                          <Clock size={12} />
                          {days === 0
                            ? lang === "TH"
                              ? "วันนี้"
                              : "Today"
                            : days === 1
                              ? lang === "TH"
                                ? "พรุ่งนี้"
                                : "Tomorrow"
                              : `${days}d`}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Past */}
            {past.length > 0 && (
              <div>
                <p
                  className="text-xs font-black tracking-widest uppercase mb-3 pl-1"
                  style={{ color: "var(--text-dim)" }}
                >
                  {lang === "TH" ? "ผ่านไปแล้ว" : "PAST"} ({past.length})
                </p>
                <div className="space-y-2 opacity-60">
                  {past.map((e) => (
                    <div
                      key={e.ticker}
                      className="border rounded-2xl p-3 flex items-center gap-4"
                      style={{
                        background: "var(--bg-card)",
                        borderColor: "var(--border-subtle)",
                      }}
                    >
                      <img
                        src={logoUrl(e.ticker)}
                        alt=""
                        className="w-8 h-8 rounded-full border border-white/10"
                        onError={(ev) => {
                          (ev.target as HTMLImageElement).style.display =
                            "none";
                        }}
                      />
                      <div className="flex-1">
                        <p
                          className="font-bold text-sm"
                          style={{ color: "var(--text-secondary)" }}
                        >
                          {e.ticker}
                        </p>
                      </div>
                      <span
                        className="text-xs tabular-nums"
                        style={{ color: "var(--text-dim)" }}
                      >
                        {dateLabel(e.date, lang)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </ProGate>
  );
}
