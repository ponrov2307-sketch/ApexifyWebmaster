"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-store";
import { useTheme } from "@/lib/theme-store";
import Sidebar from "@/components/sidebar";
import Header from "@/components/header";
import TickerTape from "@/components/ticker-tape";
import CopilotFab from "@/components/copilot-fab";
import NotificationCenter from "@/components/notification-center";
import DailySummaryPopup from "@/components/daily-summary-popup";
import { Loader2 } from "lucide-react";
import api from "@/lib/api";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, loading, loadFromStorage, refreshUser } = useAuth();
  const { theme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [notifOpen, setNotifOpen] = useState(false);

  // Sync theme attribute on mount and changes
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    loadFromStorage();
    refreshUser(); // sync role from server in case it changed since last login
  }, [loadFromStorage, refreshUser]);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  // Heartbeat — update last_seen every 60s so admin can see who's online
  useEffect(() => {
    if (!user) return;
    const ping = () => api.post("/api/admin/heartbeat").catch(() => {});
    // Delay first ping 5s to not compete with initial data load
    const firstPing = setTimeout(ping, 5000);
    const id = setInterval(ping, 60_000);

    // Clear presence immediately when tab closes
    const handleUnload = () => {
      const token = localStorage.getItem("access_token");
      if (token) {
        fetch("/api/admin/offline", {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          keepalive: true,
        }).catch(() => {});
      }
    };
    window.addEventListener("beforeunload", handleUnload);

    return () => {
      clearTimeout(firstPing);
      clearInterval(id);
      window.removeEventListener("beforeunload", handleUnload);
    };
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center themed-bg">
        <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen themed-bg" style={{ background: 'var(--bg-primary)' }}>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <Header
        onMenuClick={() => setSidebarOpen(!sidebarOpen)}
        sidebarOpen={sidebarOpen}
        onNotificationClick={() => setNotifOpen(true)}
      />
      <TickerTape />

      {/* Main content — offset for sidebar + ticker tape */}
      <main className={`pt-[96px] min-h-screen transition-all duration-300 ${sidebarOpen ? "lg:pl-64" : ""}`}>
        <div className="p-4 md:p-6">{children}</div>
      </main>

      <CopilotFab />
      <NotificationCenter open={notifOpen} onClose={() => setNotifOpen(false)} />
      <DailySummaryPopup />
    </div>
  );
}
