"use client";

import { Shield, AlertTriangle, Target, Crown } from "lucide-react";
import { Lang, tr } from "@/lib/i18n";
import { HealthScore as HealthScoreType } from "@/lib/dashboard-helpers";

interface Props {
  health: HealthScoreType;
  isProPlan: boolean;
  lang: Lang;
}

export default function HealthScorePanel({ health, isProPlan, lang }: Props) {
  return (
    <div className="rounded-[22px] border border-white/5 p-5 md:p-6 space-y-4"
      style={{ background: "linear-gradient(180deg, rgba(14,25,35,0.9), rgba(9,16,24,0.92))", backdropFilter: "blur(14px)", boxShadow: "0 14px 34px rgba(0,0,0,0.42), inset 0 1px 0 rgba(255,255,255,0.06)" }}
    >
      <div className="flex justify-between items-center flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Shield size={16} className="text-[#39C8FF]" />
          <p className="text-xs md:text-sm font-black text-[#39C8FF] tracking-widest uppercase">{tr("health.title", lang)}</p>
        </div>
        <span className="text-sm font-black text-white px-3 py-1 rounded-full bg-[#39C8FF]/15 border border-[#39C8FF]/30">
          Score {health.score}/100
        </span>
      </div>

      {isProPlan ? (
        <>
          <div className="flex flex-wrap gap-2">
            {Object.entries(health.subscores).map(([key, val]) => {
              const badge = val >= 70 ? "#32D74B" : val >= 45 ? "#FCD535" : "#FF453A";
              return (
                <div key={key} className="flex-1 min-w-[140px] bg-white/5 rounded-xl border border-white/10 p-3">
                  <p className="text-[10px] text-gray-500 font-black tracking-widest uppercase">{key}</p>
                  <p className="text-lg font-black" style={{ color: badge }}>{val}/100</p>
                </div>
              );
            })}
          </div>

          <div className="space-y-2">
            <p className="text-[10px] text-gray-500 font-black tracking-widest uppercase">Top Issues</p>
            {health.issues.map((issue, i) => (
              <div key={i} className="flex items-start gap-2">
                <AlertTriangle size={12} className="text-[#FCD535] mt-0.5 shrink-0" />
                <p className="text-xs text-gray-300">{issue}</p>
              </div>
            ))}
            <p className="text-[10px] text-gray-500 font-black tracking-widest uppercase mt-2">Action Plan</p>
            {health.actions.map((action, i) => (
              <div key={i} className="flex items-start gap-2">
                <Target size={12} className="text-[#20D6A1] mt-0.5 shrink-0" />
                <p className="text-xs text-[#20D6A1]">{action}</p>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="space-y-3">
          {health.issues.length > 0 && (
            <div className="flex items-start gap-2">
              <AlertTriangle size={12} className="text-[#FCD535] mt-0.5 shrink-0" />
              <p className="text-xs text-gray-300">{health.issues[0]}</p>
            </div>
          )}
          {health.actions.length > 0 && (
            <div className="flex items-start gap-2">
              <Target size={12} className="text-[#20D6A1] mt-0.5 shrink-0" />
              <p className="text-xs text-[#20D6A1]">{health.actions[0]}</p>
            </div>
          )}
          <div className="flex items-center justify-center pt-1">
            <button onClick={() => window.open("/payment", "_self")}
              className="flex items-center gap-1.5 px-5 py-2 bg-[#FCD535] text-black font-black rounded-full text-xs hover:scale-105 transition-transform shadow-[0_0_15px_rgba(252,213,53,0.3)]">
              <Crown size={12} /> UNLOCK FULL ANALYSIS
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
