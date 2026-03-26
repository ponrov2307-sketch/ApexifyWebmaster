import { create } from "zustand";

export type Lang = "TH" | "EN";

interface LangState {
  lang: Lang;
  setLang: (lang: Lang) => void;
  toggle: () => void;
}

export const useLang = create<LangState>((set, get) => ({
  lang: (typeof window !== "undefined" ? (localStorage.getItem("lang") as Lang) : null) || "TH",
  setLang: (lang) => {
    localStorage.setItem("lang", lang);
    set({ lang });
  },
  toggle: () => {
    const next = get().lang === "TH" ? "EN" : "TH";
    localStorage.setItem("lang", next);
    set({ lang: next });
  },
}));

/* ─── Translation dictionary ─── */
const dict: Record<string, { TH: string; EN: string }> = {
  // Dashboard
  "dashboard.welcome": { TH: "ยินดีต้อนรับ", EN: "Welcome" },
  "dashboard.total_portfolio_value": { TH: "มูลค่าพอร์ตรวม", EN: "Total Portfolio Value" },
  "dashboard.add_holding": { TH: "เพิ่มสินทรัพย์", EN: "Add Asset" },
  "dashboard.current_portfolio": { TH: "พอร์ตการลงทุนปัจจุบัน", EN: "Current Portfolio" },
  "dashboard.command_center": { TH: "ศูนย์ควบคุม", EN: "Command Center" },
  "dashboard.holdings": { TH: "สินทรัพย์", EN: "Holdings" },
  "dashboard.no_package": { TH: "ยังไม่มีแพ็กเกจ", EN: "No package" },
  "dashboard.status.ready": { TH: "พร้อมใช้งาน", EN: "Ready" },

  // Sidebar
  "router.main_menu": { TH: "เมนูหลัก", EN: "MAIN MENU" },
  "router.pro_tools": { TH: "เครื่องมือ PRO", EN: "PRO TOOLS" },
  "router.market_pulse": { TH: "ชีพจรตลาด", EN: "MARKET PULSE" },
  "router.macro_hud": { TH: "Macro HUD", EN: "Macro HUD" },
  "router.main_site": { TH: "เว็บหลัก", EN: "MAIN SITE" },

  // Menu items
  "menu.dashboard": { TH: "แดชบอร์ด", EN: "Dashboard" },
  "menu.analytics": { TH: "วิเคราะห์พอร์ต", EN: "Analytics" },
  "menu.matchmaker": { TH: "จับคู่หุ้น AI", EN: "Matchmaker" },
  "menu.dividend": { TH: "ปันผล", EN: "Dividend" },
  "menu.heatmap": { TH: "แผนที่ความร้อน", EN: "Heatmap" },
  "menu.simulator": { TH: "จำลองผลตอบแทน", EN: "Simulator" },
  "menu.alerts": { TH: "แจ้งเตือนราคา", EN: "Alerts" },
  "menu.news": { TH: "ข่าวสาร", EN: "News" },
  "menu.earnings": { TH: "ปฏิทินงบ", EN: "Earnings" },
  "menu.benchmark": { TH: "เทียบ Benchmark", EN: "Benchmark" },
  "menu.export": { TH: "ส่งออกข้อมูล", EN: "Export" },
  "menu.upgrade": { TH: "อัปเกรด", EN: "Upgrade" },

  // Trade Plan
  "trade_plan.title": { TH: "แผนการเทรด", EN: "Trade Plan" },
  "trade_plan.subtitle": { TH: "วิเคราะห์จุดเข้า/ออก โดย AI", EN: "AI-powered entry/exit analysis" },

  // Health Score
  "health.title": { TH: "สุขภาพพอร์ต", EN: "Portfolio Health" },

  // Payment
  "payment.title": { TH: "ปลดล็อกพลังเต็มรูปแบบ", EN: "UNLOCK APEX MASTERY" },
  "payment.subtitle": { TH: "เลือกแพ็กเกจที่ใช่สำหรับคุณ", EN: "Choose Your Institutional Plan" },
  "payment.monthly": { TH: "รายเดือน", EN: "Monthly" },
  "payment.yearly": { TH: "รายปี (ประหยัด 20%)", EN: "Yearly (Save 20%)" },
  "payment.basic.name": { TH: "BASIC", EN: "BASIC" },
  "payment.basic.cta": { TH: "เริ่มต้นใช้งานฟรี", EN: "Start Free" },
  "payment.vip.name": { TH: "VIP", EN: "VIP" },
  "payment.vip.cta": { TH: "อัปเกรด VIP", EN: "Upgrade VIP" },
  "payment.pro.name": { TH: "PRO", EN: "PRO" },
  "payment.pro.cta": { TH: "อัปเกรด PRO", EN: "Upgrade PRO" },
  "payment.send_slip": { TH: "ส่งสลิปใน TELEGRAM", EN: "Send Slip via TELEGRAM" },
  "payment.how_to": { TH: "วิธีอัปเกรด", EN: "How to upgrade" },
  "payment.how_to_desc": {
    TH: "โอนเงินตามแพ็กเกจ แล้วส่งสลิปให้บอท AI ตรวจสอบและอัปเกรดอัตโนมัติ",
    EN: "Transfer the amount and send the slip to our bot for automatic verification and upgrade",
  },

  // Features
  "feature.market_summary": { TH: "สรุปสภาวะตลาดโลก", EN: "Global market summary" },
  "feature.news_alerts": { TH: "ข่าวด่วนการลงทุน", EN: "Investment news alerts" },
  "feature.watchlist_3": { TH: "Watchlist สูงสุด 3 ตัว", EN: "Watchlist max 3 tickers" },
  "feature.chart_10": { TH: "วิเคราะห์กราฟ 10 ครั้ง/วัน", EN: "Chart analysis 10 times/day" },
  "feature.all_basic": { TH: "ทุกฟีเจอร์ BASIC", EN: "All BASIC features" },
  "feature.unlimited_chart": { TH: "สแกนกราฟไม่จำกัด (RSI, MACD, Vol)", EN: "Unlimited graph scanning (RSI, MACD, Vol)" },
  "feature.watchlist_10": { TH: "Watchlist สูงสุด 10 ตัว", EN: "Watchlist max 10 tickers" },
  "feature.ai_sr": { TH: "AI คำนวณ Support/Resistance อัตโนมัติ", EN: "AI automatic S/R calculation" },
  "feature.trade_plan": { TH: "AI Trade Plan พร้อมจุด Entry/TP/SL", EN: "AI Trade Plan with Entry/TP/SL" },
  "feature.all_vip": { TH: "ทุกฟีเจอร์ VIP", EN: "All VIP features" },
  "feature.matchmaker": { TH: "AI Stock Matchmaker", EN: "AI Stock Matchmaker" },
  "feature.morning_brief": { TH: "สรุปตลาดรายวัน (Morning Briefing)", EN: "Morning briefing (daily summary)" },
  "feature.custom_alerts": { TH: "แจ้งเตือนราคาแบบกำหนดเอง", EN: "Custom price alerts" },
  "feature.global_news": { TH: "ข่าวด่วนระดับโลก", EN: "Global news alerts" },
  "feature.unlimited_watchlist": { TH: "Watchlist ไม่จำกัด", EN: "Unlimited watchlist" },

  // Copilot
  "copilot.fab": { TH: "Apexify Copilot", EN: "Apexify Copilot" },
  "copilot.title": { TH: "APEXIFY COPILOT", EN: "APEXIFY COPILOT" },
  "copilot.upgrade_btn": { TH: "อัปเกรดเป็น PRO", EN: "UPGRADE TO PRO" },
  "copilot.placeholder": { TH: "ถามเกี่ยวกับพอร์ตของคุณ...", EN: "Ask about your portfolio..." },

  // Dashboard filters
  "dashboard.all": { TH: "ทั้งหมด", EN: "ALL" },
  "dashboard.sort.az": { TH: "ชื่อ", EN: "A-Z" },
  "dashboard.sort.profit": { TH: "กำไร%", EN: "Profit%" },
  "dashboard.sort.value": { TH: "มูลค่า", EN: "Value" },

  // Morning Briefing
  "morning.title": { TH: "สรุปตลาดประจำวัน", EN: "Morning Briefing" },
  "morning.subtitle": { TH: "สรุป AI รายวันก่อนเปิดตลาด", EN: "AI-powered daily market summary" },
  "morning.generate": { TH: "สร้างสรุปวันนี้", EN: "Generate Today's Brief" },
  "morning.regenerate": { TH: "สร้างใหม่", EN: "Regenerate" },

  // Macro
  "macro.title": { TH: "Macro HUD", EN: "Macro HUD" },
  "macro.subtitle": { TH: "แดชบอร์ดความเสี่ยงตลาดโลก", EN: "Global market risk dashboard" },

  // Dividend
  "dividend.title": { TH: "ติดตามปันผล", EN: "Dividend Tracker" },
  "dividend.subtitle": { TH: "รายได้ปันผลจากพอร์ตของคุณ", EN: "Dividend income from your portfolio" },

  // Matchmaker
  "matchmaker.title": { TH: "จับคู่หุ้น AI", EN: "AI Matchmaker" },
  "matchmaker.subtitle": { TH: "AI แนะนำหุ้นตามพอร์ตของคุณ", EN: "AI-powered recommendations based on your portfolio" },

  // Watchlist
  "watchlist.title": { TH: "Watchlist", EN: "Watchlist" },
  "watchlist.subtitle": { TH: "ติดตามหุ้นที่สนใจ", EN: "Track stocks you're interested in" },
  "watchlist.add": { TH: "เพิ่ม", EN: "Add" },

  // Common
  "common.refresh": { TH: "รีเฟรช", EN: "Refresh" },
  "common.delete": { TH: "ลบ", EN: "Delete" },
  "common.save": { TH: "บันทึก", EN: "Save" },
  "common.cancel": { TH: "ยกเลิก", EN: "Cancel" },
  "common.loading": { TH: "กำลังโหลด...", EN: "Loading..." },
  "common.no_data": { TH: "ไม่มีข้อมูล", EN: "No data" },
  "common.live": { TH: "สด", EN: "LIVE" },
  "common.live_feed": { TH: "ราคาสด", EN: "LIVE FEED" },
  "common.error": { TH: "เกิดข้อผิดพลาด", EN: "Something went wrong" },
  "common.try_again": { TH: "ลองอีกครั้ง", EN: "Try Again" },
  "common.close": { TH: "ปิด", EN: "Close" },
  "common.upgrade": { TH: "อัปเกรด", EN: "Upgrade" },
};

export function tr(key: string, lang: Lang): string {
  const entry = dict[key];
  if (!entry) return key;
  return entry[lang] || entry.EN || key;
}
