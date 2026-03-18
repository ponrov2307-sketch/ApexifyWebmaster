"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-store";
import { useLang, tr } from "@/lib/i18n";
import {
  Crown,
  Check,
  X,
  Rocket,
  Zap,
  Shield,
  MessageSquare,
  Sparkles,
  ArrowRight,
  Star,
  Gift,
} from "lucide-react";

export default function PaymentPage() {
  const user = useAuth((s) => s.user);
  const { lang } = useLang();
  const [annual, setAnnual] = useState(false);
  const currentRole = user?.role?.toLowerCase() || "free";

  const PLANS = [
    {
      name: tr("payment.basic.name", lang),
      subtitle: lang === "TH" ? "เริ่มต้นฟรี" : "Free Forever",
      priceMonthly: 0,
      priceAnnualTotal: 0,
      color: "#8B949E",
      icon: Rocket,
      roleMatch: "free",
      cta: tr("payment.basic.cta", lang),
      features: [
        { text: tr("feature.market_summary", lang), included: true },
        { text: tr("feature.news_alerts", lang), included: true },
        { text: tr("feature.watchlist_3", lang), included: true },
        { text: tr("feature.chart_10", lang), included: true },
        { text: tr("feature.ai_sr", lang), included: false },
        { text: tr("feature.trade_plan", lang), included: false },
        { text: tr("feature.matchmaker", lang), included: false },
        { text: tr("feature.unlimited_watchlist", lang), included: false },
      ],
    },
    {
      name: tr("payment.vip.name", lang),
      subtitle: lang === "TH" ? "นักลงทุนจริงจัง" : "Serious Investor",
      priceMonthly: 299,
      priceAnnualTotal: 2990,
      color: "#56D3FF",
      icon: Zap,
      popular: true,
      badge: lang === "TH" ? "ยอดนิยม" : "MOST POPULAR",
      roleMatch: "vip",
      cta: tr("payment.vip.cta", lang),
      features: [
        { text: tr("feature.all_basic", lang), included: true },
        { text: tr("feature.unlimited_chart", lang), included: true },
        { text: tr("feature.watchlist_10", lang), included: true },
        { text: tr("feature.ai_sr", lang), included: true },
        { text: tr("feature.trade_plan", lang), included: true },
        { text: tr("feature.matchmaker", lang), included: false },
        { text: tr("feature.morning_brief", lang), included: false },
        { text: tr("feature.unlimited_watchlist", lang), included: false },
      ],
    },
    {
      name: tr("payment.pro.name", lang),
      subtitle: lang === "TH" ? "ปลดล็อกทุกอย่าง" : "Unlock Everything",
      priceMonthly: 499,
      priceAnnualTotal: 4990,
      color: "#D0FD3E",
      icon: Crown,
      badge: lang === "TH" ? "คุ้มที่สุด" : "BEST VALUE",
      roleMatch: "pro",
      cta: tr("payment.pro.cta", lang),
      features: [
        { text: tr("feature.all_vip", lang), included: true },
        { text: tr("feature.matchmaker", lang), included: true },
        { text: tr("feature.morning_brief", lang), included: true },
        { text: tr("feature.custom_alerts", lang), included: true },
        { text: tr("feature.global_news", lang), included: true },
        { text: tr("feature.unlimited_watchlist", lang), included: true },
      ],
    },
  ];

  return (
    <div className="max-w-5xl mx-auto relative">
      {/* Animated background elements */}
      <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full blur-[200px] bg-gradient-to-r from-[#D0FD3E]/8 via-[#56D3FF]/8 to-[#D0FD3E]/5 pointer-events-none animate-pulse" />
      <div className="absolute top-60 -right-20 w-[400px] h-[400px] rounded-full blur-[150px] bg-[#56D3FF]/5 pointer-events-none" />
      <div className="absolute top-80 -left-20 w-[300px] h-[300px] rounded-full blur-[120px] bg-[#D0FD3E]/5 pointer-events-none" />

      {/* Header */}
      <div className="text-center mb-12 relative">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-px h-8 bg-gradient-to-b from-transparent to-[#D0FD3E]/50" />
          <div className="flex items-center gap-2">
            <Sparkles className="text-[#D0FD3E] animate-pulse" size={16} />
            <span className="text-[10px] font-black tracking-[0.5em] text-[#D0FD3E]/60 uppercase">
              {lang === "TH" ? "อัปเกรดประสบการณ์" : "Upgrade Your Experience"}
            </span>
            <Sparkles className="text-[#D0FD3E] animate-pulse" size={16} />
          </div>
          <div className="w-px h-8 bg-gradient-to-b from-[#D0FD3E]/50 to-transparent" />
        </div>

        <h1 className="text-4xl md:text-6xl font-black text-white tracking-tight mb-4 leading-tight">
          {lang === "TH" ? (
            <>
              ปลดล็อก<span className="text-[#D0FD3E]">พลังเต็ม</span>รูปแบบ
            </>
          ) : (
            <>
              Unlock <span className="text-[#D0FD3E]">Full Power</span>
            </>
          )}
        </h1>
        <p className="text-gray-500 text-base max-w-lg mx-auto leading-relaxed">
          {lang === "TH"
            ? "เครื่องมือวิเคราะห์ระดับสถาบัน AI อัจฉริยะ และสิทธิพิเศษมากมาย"
            : "Institutional-grade analytics, intelligent AI, and exclusive features"}
        </p>

        {/* Billing toggle */}
        <div className="flex items-center justify-center mt-8">
          <div className="bg-[#0D1117] border border-white/10 rounded-2xl p-1.5 flex gap-1 relative shadow-[0_4px_20px_rgba(0,0,0,0.3)]">
            <button
              onClick={() => setAnnual(false)}
              className={`px-7 py-3 rounded-xl text-sm font-black transition-all relative z-10 ${
                !annual
                  ? "bg-white text-black shadow-lg"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {tr("payment.monthly", lang)}
            </button>
            <button
              onClick={() => setAnnual(true)}
              className={`px-7 py-3 rounded-xl text-sm font-black transition-all relative z-10 flex items-center gap-2 ${
                annual
                  ? "bg-[#D0FD3E] text-black shadow-lg"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {tr("payment.yearly", lang)}
              <span
                className={`text-[10px] font-black px-2.5 py-1 rounded-full ${
                  annual ? "bg-black/20 text-black" : "bg-[#D0FD3E]/20 text-[#D0FD3E]"
                }`}
              >
                <Gift size={10} className="inline mr-0.5" />
                -20%
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Pricing cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        {PLANS.map((plan) => {
          const isCurrent =
            (plan.roleMatch === "free" && currentRole === "free") ||
            (plan.roleMatch === "vip" && currentRole === "vip") ||
            (plan.roleMatch === "pro" && (currentRole === "pro" || currentRole === "admin"));

          const displayPrice = annual ? plan.priceAnnualTotal : plan.priceMonthly;
          const perMonth =
            annual && plan.priceAnnualTotal > 0
              ? Math.round(plan.priceAnnualTotal / 12)
              : null;

          const isHighlight = plan.popular || plan.roleMatch === "pro";

          return (
            <div
              key={plan.name}
              className={`rounded-[32px] overflow-hidden relative flex flex-col transition-all duration-500 hover:scale-[1.03] group ${
                plan.popular
                  ? "border-2 border-[#56D3FF]/50 shadow-[0_0_60px_rgba(86,211,255,0.15)] md:-mt-6 md:mb-[-24px]"
                  : plan.roleMatch === "pro"
                  ? "border-2 border-[#D0FD3E]/40 shadow-[0_0_60px_rgba(208,253,62,0.12)]"
                  : "border border-white/8 hover:border-white/15"
              }`}
            >
              {/* Animated top line */}
              <div
                className="absolute top-0 left-0 right-0 h-[3px] opacity-80"
                style={{
                  background: `linear-gradient(90deg, transparent 0%, ${plan.color} 50%, transparent 100%)`,
                }}
              />

              {/* Background glow on hover */}
              <div
                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                style={{
                  background: `radial-gradient(circle at 50% 0%, ${plan.color}08, transparent 70%)`,
                }}
              />

              <div className="bg-gradient-to-b from-[#161B22] to-[#0D1117] flex-1 flex flex-col">
                {/* Badge */}
                {plan.badge && (
                  <div className="flex justify-center pt-5">
                    <span
                      className="text-[9px] font-black tracking-[0.25em] px-5 py-2 rounded-full border flex items-center gap-1.5"
                      style={{
                        background: `${plan.color}12`,
                        color: plan.color,
                        borderColor: `${plan.color}30`,
                      }}
                    >
                      <Star size={10} fill="currentColor" />
                      {plan.badge}
                    </span>
                  </div>
                )}

                <div className="p-8 flex-1">
                  {/* Plan icon + name */}
                  <div className="flex items-center gap-3 mb-2">
                    <div
                      className="w-12 h-12 rounded-2xl flex items-center justify-center transition-transform group-hover:scale-110"
                      style={{
                        background: `${plan.color}12`,
                        border: `1px solid ${plan.color}25`,
                        boxShadow: `0 0 20px ${plan.color}10`,
                      }}
                    >
                      <plan.icon size={22} style={{ color: plan.color }} />
                    </div>
                    <div>
                      <span
                        className="text-base font-black uppercase tracking-wider"
                        style={{ color: plan.color }}
                      >
                        {plan.name}
                      </span>
                      <p className="text-gray-600 text-[11px] font-bold">{plan.subtitle}</p>
                    </div>
                  </div>

                  {/* Price */}
                  <div className="my-7 min-h-[80px]">
                    {displayPrice === 0 ? (
                      <div>
                        <span className="text-5xl font-black text-white">฿0</span>
                        <span className="text-gray-500 text-sm ml-2">/mo</span>
                      </div>
                    ) : (
                      <div>
                        <div className="flex items-end gap-1">
                          <span className="text-5xl font-black text-white">
                            ฿{displayPrice.toLocaleString()}
                          </span>
                          <span className="text-gray-500 text-sm mb-2">
                            /{annual ? (lang === "TH" ? "ปี" : "yr") : "mo"}
                          </span>
                        </div>
                        {annual && perMonth && (
                          <p className="text-xs mt-2 font-bold" style={{ color: plan.color }}>
                            ≈ ฿{perMonth}/mo ·{" "}
                            {lang === "TH" ? "ประหยัด " : "Save "}฿
                            {(plan.priceMonthly * 12 - plan.priceAnnualTotal).toLocaleString()}
                          </p>
                        )}
                        {!annual && plan.priceAnnualTotal > 0 && (
                          <p className="text-[11px] text-gray-600 mt-2">
                            {lang === "TH" ? "หรือ " : "or "}
                            <span className="text-gray-400 font-bold">
                              ฿{plan.priceAnnualTotal.toLocaleString()}/
                              {lang === "TH" ? "ปี" : "yr"}
                            </span>{" "}
                            {lang === "TH" ? "ประหยัด 20%" : "save 20%"}
                          </p>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Divider */}
                  <div
                    className="w-full h-px mb-6"
                    style={{
                      background: `linear-gradient(90deg, transparent, ${plan.color}25, transparent)`,
                    }}
                  />

                  {/* Features */}
                  <div className="space-y-3.5">
                    {plan.features.map((f) => (
                      <div key={f.text} className="flex items-start gap-3">
                        {f.included ? (
                          <div
                            className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5"
                            style={{ background: `${plan.color}15` }}
                          >
                            <Check size={12} style={{ color: plan.color }} />
                          </div>
                        ) : (
                          <div className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 bg-white/5 mt-0.5">
                            <X size={12} className="text-gray-700" />
                          </div>
                        )}
                        <span
                          className={`text-sm leading-tight ${
                            f.included ? "text-gray-300" : "text-gray-700"
                          }`}
                        >
                          {f.text}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* CTA */}
                <div className="p-8 pt-2">
                  {isCurrent ? (
                    <div className="w-full py-4 text-center text-sm font-black text-gray-500 bg-white/5 rounded-2xl border border-white/10">
                      {lang === "TH" ? "แพ็กเกจปัจจุบัน" : "Current Plan"} ✓
                    </div>
                  ) : displayPrice === 0 ? (
                    <div className="w-full py-4 text-center text-sm font-bold text-gray-600 bg-white/3 rounded-2xl border border-white/5">
                      {plan.cta}
                    </div>
                  ) : (
                    <button
                      onClick={() =>
                        window.open("https://t.me/Apexify_Trading_bot", "_blank")
                      }
                      className="w-full py-4 text-center text-sm font-black rounded-2xl flex items-center justify-center gap-2 transition-all hover:scale-[1.04] hover:shadow-2xl group/btn relative overflow-hidden"
                      style={{
                        background: plan.color,
                        color: "#000",
                        boxShadow: `0 8px 30px ${plan.color}30`,
                      }}
                    >
                      <span className="relative z-10 flex items-center gap-2">
                        {plan.cta}
                        <ArrowRight
                          size={16}
                          className="group-hover/btn:translate-x-1 transition-transform"
                        />
                      </span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Steps guide */}
      <div className="bg-gradient-to-br from-[#161B22] to-[#0D1117] border border-white/8 rounded-[32px] p-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[#D0FD3E]/20 to-transparent" />

        <div className="text-center mb-8">
          <h3 className="text-2xl font-black text-white mb-2">
            {lang === "TH" ? "วิธีอัปเกรด" : "How to Upgrade"}
          </h3>
          <p className="text-gray-500 text-sm">
            {lang === "TH" ? "3 ขั้นตอนง่ายๆ" : "3 simple steps"}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {[
            {
              step: "01",
              icon: Shield,
              color: "#D0FD3E",
              title: lang === "TH" ? "โอนเงิน" : "Transfer",
              desc:
                lang === "TH"
                  ? "โอนเงินตามแพ็กเกจที่เลือก"
                  : "Transfer the amount for your plan",
            },
            {
              step: "02",
              icon: MessageSquare,
              color: "#56D3FF",
              title: lang === "TH" ? "ส่งสลิป" : "Send Slip",
              desc:
                lang === "TH"
                  ? "ส่งสลิปผ่าน Telegram Bot"
                  : "Send your payment slip via Telegram Bot",
            },
            {
              step: "03",
              icon: Zap,
              color: "#32D74B",
              title: lang === "TH" ? "อัปเกรดทันที" : "Instant Upgrade",
              desc:
                lang === "TH"
                  ? "AI ตรวจสอบและอัปเกรดอัตโนมัติ"
                  : "AI verifies and upgrades automatically",
            },
          ].map((item) => (
            <div
              key={item.step}
              className="text-center p-5 bg-white/[0.02] rounded-2xl border border-white/5"
            >
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{
                  background: `${item.color}10`,
                  border: `1px solid ${item.color}20`,
                }}
              >
                <item.icon size={24} style={{ color: item.color }} />
              </div>
              <span
                className="text-[10px] font-black tracking-widest block mb-1"
                style={{ color: item.color }}
              >
                STEP {item.step}
              </span>
              <h4 className="text-white font-black text-lg mb-1">{item.title}</h4>
              <p className="text-gray-500 text-xs">{item.desc}</p>
            </div>
          ))}
        </div>

        {/* Bank details */}
        <div className="bg-[#0B0E14] border border-white/5 rounded-2xl p-6 mb-6">
          <p className="text-[10px] text-gray-500 font-black uppercase tracking-[0.25em] mb-3">
            {lang === "TH" ? "ข้อมูลการโอน" : "Bank Transfer Details"}
          </p>
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex-1">
              <p className="text-white font-black text-xl">KBank 135-1-344-691</p>
              <p className="text-gray-400 text-sm mt-0.5">
                นาย เกียรติศักดิ์ วุฒิจันทร์
              </p>
            </div>
            <div className="flex items-center gap-2 text-[#32D74B]">
              <Shield size={14} />
              <span className="text-xs font-bold">
                {lang === "TH" ? "ปลอดภัย 100%" : "100% Secure"}
              </span>
            </div>
          </div>
        </div>

        {/* CTA */}
        <button
          onClick={() =>
            window.open("https://t.me/Apexify_Trading_bot", "_blank")
          }
          className="w-full sm:w-auto mx-auto flex items-center justify-center gap-2 px-10 py-4 bg-[#32D74B] text-black font-black rounded-2xl text-sm hover:scale-[1.04] transition-transform shadow-[0_8px_30px_rgba(50,215,75,0.3)]"
        >
          <MessageSquare size={16} />
          {tr("payment.send_slip", lang)}
        </button>
      </div>
    </div>
  );
}
