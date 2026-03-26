"use client";

import { useState, useEffect } from "react";
import { useLang } from "@/lib/i18n";
import api from "@/lib/api";
import { CalendarDays, Loader2, Clock, Flame, Landmark, Briefcase, TrendingUp } from "lucide-react";
import ProGate from "@/components/pro-gate";

interface EconEvent {
  date: string;
  event: string;
  category: string;
  impact: string;
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

const CATEGORY_CONFIG: Record<string, { icon: typeof Flame; color: string; label: { TH: string; EN: string } }> = {
  fed: { icon: Landmark, color: "#AF52DE", label: { TH: "Fed/FOMC", EN: "Fed/FOMC" } },
  inflation: { icon: Flame, color: "#FF9500", label: { TH: "เงินเฟ้อ", EN: "Inflation" } },
  employment: { icon: Briefcase, color: "#39C8FF", label: { TH: "การจ้างงาน", EN: "Employment" } },
  gdp: { icon: TrendingUp, color: "#32D74B", label: { TH: "GDP", EN: "GDP" } },
};

function ImpactDots({ impact }: { impact: string }) {
  const count = impact === "high" ? 3 : impact === "medium" ? 2 : 1;
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="w-1.5 h-1.5 rounded-full"
          style={{
            background: i <= count
              ? count === 3 ? "#FF453A" : count === 2 ? "#FF9500" : "#8B949E"
              : "var(--input-bg)",
          }}
        />
      ))}
    </div>
  );
}

export default function EconomicCalendarPage() {
  const { lang } = useLang();
  const [events, setEvents] = useState<EconEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    api
      .get<{ events: EconEvent[] }>("/api/market/economic-calendar")
      .then(({ data }) => setEvents(data.events || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter === "all" ? events : events.filter((e) => e.category === filter);
  const upcoming = filtered.filter((e) => daysUntil(e.date) >= 0);
  const past = filtered.filter((e) => daysUntil(e.date) < 0);

  // Group upcoming by month
  const groupedUpcoming: Record<string, EconEvent[]> = {};
  for (const e of upcoming) {
    const month = new Date(e.date + "T00:00:00").toLocaleDateString(lang === "TH" ? "th-TH" : "en-US", {
      month: "long",
      year: "numeric",
    });
    if (!groupedUpcoming[month]) groupedUpcoming[month] = [];
    groupedUpcoming[month].push(e);
  }

  return (
    <ProGate>
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-5">
          <h1
            className="text-2xl font-black tracking-wide flex items-center gap-3"
            style={{ color: "var(--text-primary)" }}
          >
            <CalendarDays className="text-[#AF52DE]" size={24} />
            {lang === "TH" ? "ปฏิทินเศรษฐกิจ" : "Economic Calendar"}
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            {lang === "TH"
              ? "FOMC, CPI, Non-Farm Payrolls, GDP — อีเวนต์สำคัญที่กระทบตลาด"
              : "Key market-moving events: FOMC, CPI, NFP, GDP"}
          </p>
        </div>

        {/* Category filters */}
        <div className="flex flex-wrap gap-2 mb-5">
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${
              filter === "all"
                ? "bg-white/10 border-white/20 text-white"
                : "border-transparent text-gray-500 hover:text-white hover:bg-white/5"
            }`}
          >
            {lang === "TH" ? "ทั้งหมด" : "All"}
          </button>
          {Object.entries(CATEGORY_CONFIG).map(([key, cfg]) => {
            const Icon = cfg.icon;
            return (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${
                  filter === key
                    ? "border-current"
                    : "border-transparent text-gray-500 hover:bg-white/5"
                }`}
                style={filter === key ? { color: cfg.color, background: `${cfg.color}15`, borderColor: `${cfg.color}30` } : undefined}
              >
                <Icon size={12} />
                {cfg.label[lang]}
              </button>
            );
          })}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
          </div>
        ) : (
          <>
            {/* Upcoming grouped by month */}
            {Object.entries(groupedUpcoming).map(([month, monthEvents]) => (
              <div key={month} className="mb-6">
                <p
                  className="text-xs font-black tracking-widest uppercase mb-3 pl-1"
                  style={{ color: "var(--text-muted)" }}
                >
                  {month}
                </p>
                <div className="space-y-2">
                  {monthEvents.map((e, i) => {
                    const days = daysUntil(e.date);
                    const cfg = CATEGORY_CONFIG[e.category] || CATEGORY_CONFIG.gdp;
                    const Icon = cfg.icon;
                    const isToday = days === 0;
                    const isThisWeek = days > 0 && days <= 7;

                    return (
                      <div
                        key={`${e.date}-${i}`}
                        className="border rounded-2xl p-4 flex items-center gap-4 transition-all hover:brightness-110"
                        style={{
                          background: isToday
                            ? `${cfg.color}08`
                            : "var(--bg-card)",
                          borderColor: isToday
                            ? `${cfg.color}30`
                            : "var(--border-default)",
                        }}
                      >
                        {/* Category icon */}
                        <div
                          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                          style={{ background: `${cfg.color}15` }}
                        >
                          <Icon size={18} style={{ color: cfg.color }} />
                        </div>

                        {/* Event info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <p className="font-black text-sm" style={{ color: "var(--text-primary)" }}>
                              {e.event}
                            </p>
                            <ImpactDots impact={e.impact} />
                          </div>
                          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                            {dateLabel(e.date, lang)}
                          </p>
                        </div>

                        {/* Countdown */}
                        <div
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-black shrink-0"
                          style={{
                            background: isToday
                              ? `${cfg.color}20`
                              : isThisWeek
                                ? "rgba(255,149,0,0.1)"
                                : "var(--input-bg)",
                            color: isToday
                              ? cfg.color
                              : isThisWeek
                                ? "#FF9500"
                                : "var(--text-muted)",
                            border: `1px solid ${isToday ? `${cfg.color}30` : isThisWeek ? "rgba(255,149,0,0.2)" : "var(--border-default)"}`,
                          }}
                        >
                          <Clock size={11} />
                          {isToday
                            ? lang === "TH" ? "วันนี้" : "Today"
                            : days === 1
                              ? lang === "TH" ? "พรุ่งนี้" : "Tomorrow"
                              : `${days}d`}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}

            {/* Past events (collapsed) */}
            {past.length > 0 && (
              <div className="mt-4">
                <p
                  className="text-xs font-black tracking-widest uppercase mb-3 pl-1"
                  style={{ color: "var(--text-dim)" }}
                >
                  {lang === "TH" ? "ผ่านไปแล้ว" : "PAST"} ({past.length})
                </p>
                <div className="space-y-1.5 opacity-50">
                  {past.slice(-5).map((e, i) => {
                    const cfg = CATEGORY_CONFIG[e.category] || CATEGORY_CONFIG.gdp;
                    const Icon = cfg.icon;
                    return (
                      <div
                        key={`past-${e.date}-${i}`}
                        className="border rounded-xl p-3 flex items-center gap-3"
                        style={{ background: "var(--bg-card)", borderColor: "var(--border-subtle)" }}
                      >
                        <Icon size={14} style={{ color: cfg.color }} />
                        <span className="text-xs font-bold flex-1" style={{ color: "var(--text-secondary)" }}>
                          {e.event}
                        </span>
                        <span className="text-[10px] tabular-nums" style={{ color: "var(--text-dim)" }}>
                          {dateLabel(e.date, lang)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {filtered.length === 0 && (
              <div
                className="border rounded-2xl p-12 text-center"
                style={{ background: "var(--bg-card)", borderColor: "var(--border-default)" }}
              >
                <CalendarDays className="w-12 h-12 mx-auto mb-4" style={{ color: "var(--text-dim)" }} />
                <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                  {lang === "TH" ? "ไม่มีอีเวนต์" : "No events"}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </ProGate>
  );
}
