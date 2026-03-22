"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-store";
import { useLang, tr } from "@/lib/i18n";
import api from "@/lib/api";
import {
  LayoutDashboard,
  BarChart3,
  Heart,
  DollarSign,
  Grid3x3,
  TrendingUp,
  Bell,
  Newspaper,
  Download,
  Crown,
  Lock,
  Rocket,
  X,
  Activity,
  Gauge,
  Globe,
  Sun,
  Eye,
  ShieldCheck,
} from "lucide-react";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

const PRO_ROLES = ["pro", "vip", "admin"];

function fgColor(v: number) {
  if (v <= 25) return "#FF453A";
  if (v <= 45) return "#F97316";
  if (v <= 55) return "#8B949E";
  if (v <= 75) return "#FCD535";
  return "#32D74B";
}

function fgLabel(v: number, lang: "TH" | "EN") {
  if (v <= 25) return lang === "TH" ? "กลัวสุดขีด" : "EXTREME FEAR";
  if (v <= 45) return lang === "TH" ? "กลัว" : "FEAR";
  if (v <= 55) return lang === "TH" ? "เป็นกลาง" : "NEUTRAL";
  if (v <= 75) return lang === "TH" ? "โลภ" : "GREED";
  return lang === "TH" ? "โลภสุดขีด" : "EXTREME GREED";
}

function vixColor(v: number) {
  if (v < 18) return "#20D6A1";
  if (v < 25) return "#FCD535";
  return "#FF5E6C";
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuth((s) => s.user);
  const { lang } = useLang();
  const role = user?.role?.toLowerCase() || "free";
  const isPro = PRO_ROLES.includes(role);

  const [fg, setFg] = useState<{ value: number; text: string } | null>(null);
  const [vix, setVix] = useState<number | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const menuItems = [
    { icon: Eye, label: tr("watchlist.title", lang), href: "/watchlist", pro: false },
    { icon: BarChart3, label: tr("menu.analytics", lang), href: "/analytics", pro: true },
    { icon: Sun, label: tr("morning.title", lang), href: "/morning", pro: true },
    { icon: Heart, label: tr("menu.matchmaker", lang), href: "/matchmaker", pro: true },
    { icon: DollarSign, label: tr("menu.dividend", lang), href: "/dividend", pro: true },
    { icon: Grid3x3, label: tr("menu.heatmap", lang), href: "/heatmap", pro: true },
    { icon: TrendingUp, label: tr("menu.simulator", lang), href: "/sp500", pro: true },
    { icon: Bell, label: tr("menu.alerts", lang), href: "/alerts", pro: true },
    { icon: Newspaper, label: tr("menu.news", lang), href: "/news", pro: true },
    { icon: Download, label: tr("menu.export", lang), href: "/export", pro: true },
  ];

  useEffect(() => {
    const fetchMacro = async () => {
      try {
        const { data } = await api.get("/api/market/macro");
        setFg(data.fear_greed);
        setVix(data.vix);
        setLastUpdate(new Date());
      } catch {
        /* ignore */
      }
    };
    fetchMacro();
    const interval = setInterval(fetchMacro, 30000);
    return () => clearInterval(interval);
  }, []);

  const navigate = (href: string) => {
    router.push(href);
    onClose();
  };

  const updateAge = (() => {
    if (!lastUpdate) return lang === "TH" ? "กำลังอัปเดต..." : "updating...";
    const diff = Math.round((Date.now() - lastUpdate.getTime()) / 1000);
    if (diff < 10) return lang === "TH" ? "เมื่อกี้" : "just now";
    if (diff < 60) return `${diff}s ago`;
    return `${Math.floor(diff / 60)}m ago`;
  })();

  return (
    <>
      {/* Overlay — mobile only */}
      {open && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 z-50 backdrop-blur-3xl border-r shadow-[20px_0_50px_rgba(0,0,0,0.3)] transition-transform duration-300 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
        style={{ background: 'var(--sidebar-bg)', borderColor: 'var(--border-default)' }}
      >
        <div className="p-4 flex flex-col h-full overflow-y-auto">
          {/* Logo */}
          <div className="flex items-center justify-center gap-3 mb-8 mt-4">
            <Rocket className="w-6 h-6 text-[#D0FD3E] drop-shadow-[0_0_15px_rgba(208,253,62,0.6)] animate-pulse" />
            <span className="text-2xl font-black text-white tracking-[0.2em]">
              APEXIFY
            </span>
            <button
              onClick={onClose}
              className="absolute right-3 top-5 text-gray-500 hover:text-white"
            >
              <X size={20} />
            </button>
          </div>

          {/* Main */}
          <p className="text-[9px] text-gray-500 font-black mb-2 tracking-widest uppercase pl-2">
            {tr("router.main_menu", lang)}
          </p>
          <button
            onClick={() => navigate("/")}
            className={`w-full flex items-center gap-2 px-3 py-3 rounded-2xl mb-2 transition-all font-black tracking-wide ${
              pathname === "/"
                ? "text-[#D0FD3E] bg-[#D0FD3E]/10 border border-[#D0FD3E]/20 shadow-inner"
                : "text-gray-400 hover:text-white hover:bg-white/5 border border-transparent"
            }`}
          >
            <LayoutDashboard size={18} />
            <span>{tr("menu.dashboard", lang)}</span>
          </button>

          {/* Divider */}
          <div className="w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent my-4" />

          {/* Pro Tools */}
          <p className="text-[9px] text-gray-500 font-black mb-2 tracking-widest uppercase pl-2">
            {tr("router.pro_tools", lang)}
          </p>
          {menuItems.map((item) => {
            const locked = item.pro && !isPro;
            const active = pathname === item.href;
            return (
              <button
                key={item.href}
                onClick={() => navigate(item.href)}
                className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-2xl mb-1.5 transition-all relative group overflow-hidden ${
                  active
                    ? "text-[#D0FD3E] bg-[#D0FD3E]/10 border border-[#D0FD3E]/20"
                    : "text-gray-400 hover:text-white hover:bg-white/5 border border-transparent"
                }`}
              >
                <item.icon
                  size={18}
                  className="group-hover:scale-110 transition-transform"
                />
                <span className="font-bold tracking-wide">{item.label}</span>
                {locked && (
                  <Lock
                    size={14}
                    className="absolute right-4 text-[#FFD700]"
                  />
                )}
              </button>
            );
          })}

          {/* Upgrade */}
          <button
            onClick={() => navigate("/payment")}
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-2xl mb-1.5 transition-all text-[#FFD700] bg-[#FFD700]/10 border border-[#FFD700]/30 hover:bg-[#FFD700]/20"
          >
            <Crown size={18} />
            <span className="font-bold tracking-wide">{tr("menu.upgrade", lang)}</span>
          </button>

          {/* Admin panel — visible to admin only */}
          {role === "admin" && (
            <button
              onClick={() => navigate("/admin")}
              className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-2xl mb-1.5 transition-all ${
                pathname === "/admin"
                  ? "text-[#FF453A] bg-[#FF453A]/10 border border-[#FF453A]/20"
                  : "text-[#FF453A]/70 hover:text-[#FF453A] hover:bg-[#FF453A]/10 border border-transparent"
              }`}
            >
              <ShieldCheck size={18} />
              <span className="font-bold tracking-wide">Admin</span>
            </button>
          )}

          {/* Market Pulse Widget */}
          <div className="mt-auto pt-4">
            <div className="bg-[#0E1C24]/80 border border-white/10 rounded-2xl p-3 shadow-inner">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <Globe size={10} className="text-[#39C8FF]" />
                  <span className="text-[9px] text-[#39C8FF] font-black tracking-widest">
                    {tr("router.market_pulse", lang)}
                  </span>
                </div>
                <span className="text-[8px] text-gray-600">{updateAge}</span>
              </div>

              {/* Fear & Greed */}
              {fg && (
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    <Gauge size={12} style={{ color: fgColor(fg.value) }} />
                    <span className="text-[10px] text-gray-500 font-bold">
                      Fear&Greed
                    </span>
                  </div>
                  <div className="text-right">
                    <span
                      className="text-xs font-black tabular-nums block"
                      style={{ color: fgColor(fg.value), textShadow: `0 0 8px ${fgColor(fg.value)}40` }}
                    >
                      {fg.value}
                    </span>
                    <span className="text-[8px] font-bold" style={{ color: fgColor(fg.value) }}>
                      {fgLabel(fg.value, lang)}
                    </span>
                  </div>
                </div>
              )}

              {/* VIX */}
              {vix !== null && (
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    <Activity size={12} style={{ color: vixColor(vix) }} />
                    <span className="text-[10px] text-gray-500 font-bold">
                      VIX
                    </span>
                  </div>
                  <span
                    className="text-xs font-black tabular-nums"
                    style={{ color: vixColor(vix) }}
                  >
                    {vix.toFixed(2)}
                  </span>
                </div>
              )}

              {/* Macro HUD link */}
              <button
                onClick={() => navigate("/macro")}
                className="w-full text-center text-[10px] text-[#39C8FF] font-black bg-[#39C8FF]/10 px-2 py-1.5 rounded-full hover:bg-[#39C8FF]/20 transition-colors tracking-wider"
              >
                {tr("router.macro_hud", lang)}
              </button>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
