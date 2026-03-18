"use client";

import { useState, useEffect } from "react";
import { useLang } from "@/lib/i18n";
import { usePortfolio, useAlerts } from "@/lib/hooks";
import {
  Bell,
  X,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  DollarSign,
  Activity,
} from "lucide-react";

interface Props {
  open: boolean;
  onClose: () => void;
}

interface Notification {
  id: string;
  icon: React.ReactNode;
  title: string;
  body: string;
  color: string;
  time: string;
}

export default function NotificationCenter({ open, onClose }: Props) {
  const { lang } = useLang();
  const { items: portfolio, summary } = usePortfolio("USD", 0);
  const { alerts } = useAlerts();
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    if (!open) return;

    const notifs: Notification[] = [];

    // Portfolio summary notification
    if (summary && portfolio.length > 0) {
      const up = summary.total_pnl >= 0;
      notifs.push({
        id: "portfolio-summary",
        icon: up ? <TrendingUp size={14} /> : <TrendingDown size={14} />,
        title: lang === "TH" ? "สรุปพอร์ต" : "Portfolio Summary",
        body:
          lang === "TH"
            ? `มูลค่ารวม $${summary.total_value.toLocaleString("en-US", { maximumFractionDigits: 0 })} (${up ? "+" : ""}${summary.total_pnl_pct.toFixed(2)}%)`
            : `Total value $${summary.total_value.toLocaleString("en-US", { maximumFractionDigits: 0 })} (${up ? "+" : ""}${summary.total_pnl_pct.toFixed(2)}%)`,
        color: up ? "#32D74B" : "#FF453A",
        time: lang === "TH" ? "ตอนนี้" : "Now",
      });
    }

    // Top gainer
    const sorted = [...portfolio].sort((a, b) => b.pnl_pct - a.pnl_pct);
    if (sorted.length > 0 && sorted[0].pnl_pct > 0) {
      notifs.push({
        id: "top-gainer",
        icon: <TrendingUp size={14} />,
        title: lang === "TH" ? "หุ้นขึ้นเยอะสุด" : "Top Gainer",
        body: `${sorted[0].ticker} +${sorted[0].pnl_pct.toFixed(2)}%`,
        color: "#32D74B",
        time: lang === "TH" ? "ตอนนี้" : "Now",
      });
    }

    // Top loser
    if (sorted.length > 0 && sorted[sorted.length - 1].pnl_pct < 0) {
      const loser = sorted[sorted.length - 1];
      notifs.push({
        id: "top-loser",
        icon: <TrendingDown size={14} />,
        title: lang === "TH" ? "หุ้นลงเยอะสุด" : "Top Loser",
        body: `${loser.ticker} ${loser.pnl_pct.toFixed(2)}%`,
        color: "#FF453A",
        time: lang === "TH" ? "ตอนนี้" : "Now",
      });
    }

    // Active alerts
    if (alerts.length > 0) {
      notifs.push({
        id: "active-alerts",
        icon: <AlertTriangle size={14} />,
        title: lang === "TH" ? "แจ้งเตือนราคา" : "Price Alerts",
        body:
          lang === "TH"
            ? `มี ${alerts.length} แจ้งเตือนที่กำลังติดตาม`
            : `${alerts.length} active alert${alerts.length > 1 ? "s" : ""}`,
        color: "#FCD535",
        time: "",
      });
    }

    // Dividend notice
    const divStocks = portfolio.filter((p) => p.pnl_pct > 0);
    if (divStocks.length >= 3) {
      notifs.push({
        id: "dividend-tip",
        icon: <DollarSign size={14} />,
        title: lang === "TH" ? "เคล็ดลับ" : "Tip",
        body:
          lang === "TH"
            ? "ลองดูปันผลรายได้ในหน้า Dividend Tracker"
            : "Check your dividend income in the Dividend Tracker",
        color: "#56D3FF",
        time: "",
      });
    }

    setNotifications(notifs);
  }, [open, portfolio, summary, alerts, lang]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[90] flex justify-end" onClick={onClose}>
      <div
        className="w-full max-w-sm h-full bg-[#0D1117]/95 backdrop-blur-xl border-l border-white/10 shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/8">
          <div className="flex items-center gap-2">
            <Bell size={18} className="text-[#D0FD3E]" />
            <h2 className="text-lg font-black text-white">
              {lang === "TH" ? "การแจ้งเตือน" : "Notifications"}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-white p-1.5 hover:bg-white/5 rounded-lg transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Notifications list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {notifications.length === 0 ? (
            <div className="text-center py-12">
              <Activity className="w-10 h-10 text-gray-700 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">
                {lang === "TH" ? "ไม่มีการแจ้งเตือน" : "No notifications"}
              </p>
            </div>
          ) : (
            notifications.map((n) => (
              <div
                key={n.id}
                className="bg-white/[0.03] border border-white/8 rounded-xl p-3.5 hover:bg-white/[0.05] transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                    style={{ background: `${n.color}15`, color: n.color }}
                  >
                    {n.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">{n.title}</span>
                      {n.time && (
                        <span className="text-[10px] text-gray-600">{n.time}</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-400 mt-0.5">{n.body}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
