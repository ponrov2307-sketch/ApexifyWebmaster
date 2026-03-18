"use client";

import { useAuth } from "@/lib/auth-store";
import { useLang } from "@/lib/i18n";
import { useTheme } from "@/lib/theme-store";
import {
  Menu,
  Rocket,
  Globe,
  Power,
  Sun,
  Moon,
  Bell,
} from "lucide-react";

interface HeaderProps {
  onMenuClick: () => void;
  sidebarOpen?: boolean;
  onNotificationClick?: () => void;
}

export default function Header({ onMenuClick, sidebarOpen, onNotificationClick }: HeaderProps) {
  const { logout } = useAuth();
  const { lang, toggle } = useLang();
  const { theme, toggle: toggleTheme } = useTheme();

  return (
    <header className={`fixed top-0 left-0 right-0 h-[52px] z-40 backdrop-blur-2xl border-b px-4 flex justify-between items-center transition-all duration-300 ${sidebarOpen ? "lg:pl-68" : ""}`} style={{ background: 'var(--header-bg)', borderColor: 'var(--border-default)' }}>
      {/* Left */}
      <div className="flex items-center gap-2">
        <button
          onClick={onMenuClick}
          className="text-gray-400 hover:text-[#D0FD3E] transition-colors p-2 rounded-lg"
        >
          <Menu size={22} />
        </button>
        {/* Mobile logo */}
        <div className="flex items-center gap-2 cursor-pointer ml-2 lg:hidden">
          <Rocket size={16} className="text-[#D0FD3E]" />
          <span className="text-lg font-black text-white tracking-widest">
            APEX
          </span>
        </div>
      </div>

      {/* Right */}
      <div className="flex items-center gap-2 md:gap-3">
        {/* Main site link - desktop */}
        <a
          href="https://apexify-bot.vercel.app/"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden sm:flex items-center gap-1.5 text-gray-400 hover:text-white font-bold tracking-widest border border-white/10 rounded-full px-3 py-1 hover:bg-white/5 text-xs transition-colors"
        >
          <Globe size={14} />
          MAIN SITE
        </a>
        {/* Main site link - mobile */}
        <a
          href="https://apexify-bot.vercel.app/"
          target="_blank"
          rel="noopener noreferrer"
          className="sm:hidden text-gray-400 hover:text-white border border-white/10 rounded-full p-1.5 hover:bg-white/5 transition-colors"
        >
          <Globe size={14} />
        </a>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="w-8 h-8 flex items-center justify-center text-[#FCD535] border border-[#FCD535]/30 bg-[#FCD535]/10 hover:bg-[#FCD535]/20 rounded-full transition-all"
          title={theme === "dark" ? "Light mode" : "Dark mode"}
        >
          {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
        </button>

        {/* Language toggle */}
        <button
          onClick={toggle}
          className="w-8 h-8 flex items-center justify-center text-[#D0FD3E] font-black text-xs border border-[#D0FD3E]/30 bg-[#D0FD3E]/10 hover:bg-[#D0FD3E]/20 rounded-full transition-all"
          title={lang === "TH" ? "Switch to English" : "เปลี่ยนเป็นภาษาไทย"}
        >
          {lang}
        </button>

        {/* Notifications */}
        {onNotificationClick && (
          <button
            onClick={onNotificationClick}
            className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white border border-white/10 hover:bg-white/5 rounded-full transition-all relative"
          >
            <Bell size={14} />
          </button>
        )}

        {/* Logout */}
        <button
          onClick={logout}
          className="text-gray-500 hover:text-[#FF453A] hover:bg-[#FF453A]/10 transition-colors rounded-full p-2 ml-1 md:ml-0"
        >
          <Power size={18} />
        </button>
      </div>
    </header>
  );
}
