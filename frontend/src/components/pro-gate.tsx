"use client";

import { useAuth } from "@/lib/auth-store";
import { useLang, tr } from "@/lib/i18n";
import { Lock, Crown } from "lucide-react";

const PRO_ROLES = ["pro", "vip", "admin"];

interface ProGateProps {
  children: React.ReactNode;
  /** Which roles are allowed. Defaults to pro/vip/admin */
  allowedRoles?: string[];
}

/**
 * Wraps a page and shows a lock overlay if the user doesn't have the required role.
 * Matches the original NiceGUI heatmap-style blur + lock modal.
 */
export default function ProGate({ children, allowedRoles = PRO_ROLES }: ProGateProps) {
  const user = useAuth((s) => s.user);
  const { lang } = useLang();
  const role = user?.role?.toLowerCase() || "free";
  const hasAccess = allowedRoles.includes(role);

  if (hasAccess) return <>{children}</>;

  return (
    <div className="relative">
      {/* Blurred content behind */}
      <div className="blur-md pointer-events-none opacity-40 select-none">
        {children}
      </div>

      {/* Lock overlay */}
      <div className="absolute inset-0 z-20 flex items-start justify-center pt-[15vh]">
        <div className="flex flex-col items-center text-center bg-[#0B0E14]/90 backdrop-blur-md p-8 rounded-[32px] border border-[#FCD535]/30 shadow-2xl w-full max-w-sm">
          <Lock size={48} className="text-[#FCD535] mb-3" />
          <h2 className="text-xl font-black text-[#FCD535] tracking-widest">
            PREMIUM FEATURE
          </h2>
          <p className="text-gray-300 text-sm mt-2 mb-6">
            {lang === "TH"
              ? "ฟีเจอร์นี้สงวนสิทธิ์สำหรับแพ็กเกจ VIP และ PRO"
              : "This feature is reserved for VIP and PRO members"}
          </p>
          <button
            onClick={() => (window.location.href = "/payment")}
            className="w-full flex items-center justify-center gap-2 bg-[#FCD535] text-black font-black py-3 rounded-xl hover:scale-[1.02] transition-transform shadow-[0_0_20px_rgba(252,213,53,0.3)]"
          >
            <Crown size={16} />
            {lang === "TH" ? "อัปเกรดตอนนี้" : "UPGRADE NOW"}
          </button>
        </div>
      </div>
    </div>
  );
}
