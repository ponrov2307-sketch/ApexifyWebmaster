"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-store";
import api from "@/lib/api";
import { Users, RefreshCw, Shield, Crown, Zap, User } from "lucide-react";

interface OnlineUser {
  user_id: string;
  username: string;
  role: string;
  status: string;
  last_seen: string | null;
}

const ROLE_CONFIG: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  admin:   { label: "ADMIN",   color: "#FF453A", icon: Shield },
  pro:     { label: "PRO",     color: "#D0FD3E", icon: Zap },
  vip:     { label: "VIP",     color: "#FCD535", icon: Crown },
  free:    { label: "FREE",    color: "#8B949E", icon: User },
};

function timeAgo(iso: string | null): string {
  if (!iso) return "—";
  const diff = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 10) return "just now";
  if (diff < 60) return `${diff}s ago`;
  return `${Math.floor(diff / 60)}m ago`;
}

function RoleBadge({ role }: { role: string }) {
  const cfg = ROLE_CONFIG[role.toLowerCase()] ?? ROLE_CONFIG.free;
  const Icon = cfg.icon;
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-black tracking-wider"
      style={{ color: cfg.color, background: `${cfg.color}18`, border: `1px solid ${cfg.color}40` }}
    >
      <Icon size={10} />
      {cfg.label}
    </span>
  );
}

export default function AdminPage() {
  const router = useRouter();
  const user = useAuth((s) => s.user);
  const [users, setUsers] = useState<OnlineUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchOnline = useCallback(async () => {
    try {
      const { data } = await api.get<OnlineUser[]>("/api/admin/online-users");
      setUsers(data);
      setLastRefresh(new Date());
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user) return;
    if (user.role !== "admin") {
      router.replace("/");
      return;
    }
    fetchOnline();
    const id = setInterval(fetchOnline, 30_000);
    return () => clearInterval(id);
  }, [user, router, fetchOnline]);

  if (!user || user.role !== "admin") return null;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-[#D0FD3E]/10 border border-[#D0FD3E]/20 flex items-center justify-center">
            <Users size={20} className="text-[#D0FD3E]" />
          </div>
          <div>
            <h1 className="text-xl font-black text-white tracking-wide">Online Users</h1>
            <p className="text-xs text-gray-500">active in the last 2 minutes</p>
          </div>
        </div>
        <button
          onClick={fetchOnline}
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-gray-400 hover:text-white text-xs font-bold transition-all"
        >
          <RefreshCw size={13} />
          Refresh
        </button>
      </div>

      {/* Count card */}
      <div className="flex items-center gap-4">
        <div className="flex-1 bg-[#0D1117] border border-white/10 rounded-2xl p-4 flex items-center gap-3">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#32D74B] opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-[#32D74B]" />
          </span>
          <span className="text-2xl font-black text-white">{users.length}</span>
          <span className="text-sm text-gray-500 font-bold">users online</span>
          {lastRefresh && (
            <span className="ml-auto text-[10px] text-gray-600">
              updated {timeAgo(lastRefresh.toISOString())}
            </span>
          )}
        </div>
      </div>

      {/* User list */}
      <div className="bg-[#0D1117] border border-white/10 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500 text-sm">Loading...</div>
        ) : users.length === 0 ? (
          <div className="p-8 text-center text-gray-500 text-sm">No users online</div>
        ) : (
          <div className="divide-y divide-white/5">
            {users.map((u) => (
              <div key={u.user_id} className="flex items-center gap-4 px-5 py-3.5 hover:bg-white/[0.02] transition-colors">
                {/* Avatar */}
                <div className="w-9 h-9 rounded-xl bg-white/5 flex items-center justify-center text-sm font-black text-white shrink-0">
                  {u.username.slice(0, 2).toUpperCase()}
                </div>

                {/* Name + ID */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-bold text-white truncate">{u.username}</p>
                  <p className="text-[10px] text-gray-600 font-mono truncate">ID: {u.user_id}</p>
                </div>

                {/* Role */}
                <RoleBadge role={u.role} />

                {/* Last seen */}
                <span className="text-xs text-gray-500 font-mono tabular-nums w-20 text-right shrink-0">
                  {timeAgo(u.last_seen)}
                </span>

                {/* Online dot */}
                <span className="w-2 h-2 rounded-full bg-[#32D74B] shadow-[0_0_6px_#32D74B] shrink-0" />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
