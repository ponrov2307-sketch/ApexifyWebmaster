from __future__ import annotations

import re
from typing import Any, Callable


def normalize_lang(lang: str | None) -> str:
    raw = str(lang or "TH").strip().upper()
    return "TH" if raw.startswith("TH") else "EN"


_TRANSLATIONS: dict[str, dict[str, str]] = {
    "EN": {
        "dashboard.welcome": "WELCOME BACK",
        "dashboard.total_portfolio_value": "TOTAL PORTFOLIO VALUE",
        "dashboard.add_holding": "+ ADD HOLDING",
        "dashboard.current_portfolio": "CURRENT PORTFOLIO",
        "dashboard.status.valid_till": "Valid till: {date}",
        "dashboard.status.valid_short": "Valid: {date}",
        "dashboard.status.ready": "Ready to trade",
        "dashboard.holdings": "YOUR HOLDINGS",
        "dashboard.filter": "Portfolio Filter",
        "dashboard.assets_count": "{count} assets",
        "dashboard.command_center": "VIP COMMAND CENTER",
        "dashboard.days_left": "{days} DAYS LEFT",
        "dashboard.no_package": "NO ACTIVE PACKAGE",
        "dashboard.empty_group_title": "No holdings in {group} group.",
        "dashboard.empty_group_subtitle": "This filter currently has no assets.",
        "dashboard.empty_group_cta": "Change filter or edit asset group.",
        "dashboard.price_feed_warning": "Price feed delayed for {count} symbols, using Avg Cost temporarily{suffix}",
        "dashboard.sort.az": "A-Z",
        "dashboard.sort.profit": "PROFIT",
        "dashboard.sort.value": "VALUE",
        "trade_plan.title": "PRO TRADE PLAN BUILDER",
        "trade_plan.subtitle": "Heuristic decision guide for each holding",
        "trade_plan.legend": (
            "Legend: Profit=%PnL vs cost, Entry=entry zone, TP1/TP2=take-profit, "
            "SL=stop-loss, R:R=reward/risk, PosRisk=%risk per position"
        ),
        "trade_plan.preview": "PRO PREVIEW",
        "trade_plan.unlock": "UNLOCK FULL TRADE PLAN",
        "trade_plan.no_preview": "No holdings available for preview.",
        "trade_plan.create_alert": "Create Alert",
        "trade_plan.view_chart": "View Chart",
        "health.title": "PORTFOLIO HEALTH SCORE",
        "health.top_issues": "TOP ISSUES",
        "health.action_plan": "ACTION PLAN",
        "health.what_if": "What-if score after fixes: {score}/100",
        "health.uplift": "Potential uplift: +{delta}",
        "health.mode": "Mode: Balanced Retail",
        "health.no_holdings": "No holdings available.",
        "health.no_holdings_action": "Add holdings to generate a health diagnosis.",
        "health.zero_value": "Portfolio value is zero.",
        "health.zero_value_action": "Update prices/holdings before diagnosis.",
        "health.balanced": "Portfolio structure is balanced with manageable risk.",
        "health.balanced_action": "Keep allocation discipline and review risk weekly.",
        "health.issue.concentration": "Concentration risk: top position is {value:.1f}% of portfolio.",
        "health.issue.drawdown": "Drawdown pressure: {value:.1f}% of portfolio is in losing positions.",
        "health.issue.volatility": "Downside volatility is elevated in current portfolio.",
        "health.issue.correlation": "Correlation proxy risk: top 3 holdings = {value:.1f}%.",
        "health.action.concentration": "Trim top position and spread into 2-3 uncorrelated names.",
        "health.action.drawdown": "Set stop-loss rules and reduce persistent weak trends.",
        "health.action.volatility": "Reduce high-beta exposure and rebalance to lower-volatility assets.",
        "health.action.correlation": "Diversify sectors/themes to reduce same-direction shocks.",
        "health.sub.concentration": "Concentration",
        "health.sub.drawdown": "Drawdown",
        "health.sub.volatility": "Volatility",
        "health.sub.correlation": "Correlation",
        "health.penalty.breakdown": "Penalty breakdown",
        "health.issue_prefix": "Issue:",
        "health.action_prefix": "Action:",
        "health.unlock_full": "UNLOCK FULL HEALTH DIAGNOSIS",
        "health.teaser_issue": "Risk diagnosis available in PRO",
        "health.teaser_action": "Unlock PRO for full action plan",
        "table.empty.title": "No assets found.",
        "table.empty.subtitle": "Click + ADD HOLDING to start your journey.",
        "table.lock.ai": "Upgrade to PRO to unlock AI stock insights",
        "table.meta.price": "Price",
        "table.meta.avg": "Avg",
        "table.meta.hold": "Hold",
        "charts.locked_timeframe": "Locked timeframe (1W, 1M) is available for VIP/PRO only.",
        "charts.data_feed_unavailable": "Data feed unavailable for {ticker} ({interval}). Please try another timeframe or retry later.",
        "charts.data_feed_unavailable_short": "Data feed unavailable\nPlease retry in a moment",
        "charts.load_failed": "Unable to load chart data for {ticker} ({interval})",
        "router.feature_locked": "Feature {feature} is for PRO. Upgrade to unlock.",
        "router.main_menu": "MAIN MENU",
        "router.pro_tools": "PRO TOOLS",
        "router.menu.dashboard": "Dashboard",
        "router.menu.analytics": "Analytics",
        "router.menu.matchmaker": "AI Matchmaker",
        "router.menu.dividend": "Dividend",
        "router.menu.heatmap": "Heatmap",
        "router.menu.simulator": "2-Stock Simulator",
        "router.menu.alerts": "Price Alerts",
        "router.menu.export": "Export",
        "router.menu.upgrade": "Upgrade PRO",
        "router.market_pulse": "MARKET PULSE",
        "router.loading": "Loading",
        "router.updated_initial": "Updated ...",
        "router.updated_age": "Updated {age}",
        "router.macro_hud": "Macro HUD",
        "router.main_site": "MAIN SITE",
        "copilot.title": "APEXIFY COPILOT",
        "copilot.fab": "Apexify Copilot",
        "copilot.placeholder": 'Ask AI, e.g. "Analyze TSLA briefly"',
        "copilot.upgrade_body": "**Copilot is a PRO/VIP feature.**\n\nUpgrade to use live AI on web.",
        "copilot.upgrade_btn": "UPGRADE TO PRO",
        "copilot.thinking": "Copilot is thinking...",
        "copilot.send": "Send",
        "copilot.open_gemini": "Open Gemini Page",
        "auth.login_success": "Login success",
        "auth.token_disabled": "Token login is disabled.",
    },
    "TH": {
        "dashboard.welcome": "ยินดีต้อนรับ",
        "dashboard.total_portfolio_value": "มูลค่าพอร์ตรวม",
        "dashboard.add_holding": "+ เพิ่มสินทรัพย์",
        "dashboard.current_portfolio": "พอร์ตปัจจุบัน",
        "dashboard.status.valid_till": "ใช้งานได้ถึง: {date}",
        "dashboard.status.valid_short": "ถึง: {date}",
        "dashboard.status.ready": "พร้อมเทรด",
        "dashboard.holdings": "สินทรัพย์ของคุณ",
        "dashboard.filter": "ตัวกรองพอร์ต",
        "dashboard.assets_count": "{count} รายการ",
        "dashboard.command_center": "ศูนย์ควบคุมสมาชิก",
        "dashboard.days_left": "เหลือ {days} วัน",
        "dashboard.no_package": "ไม่มีแพ็กเกจที่ใช้งานอยู่",
        "dashboard.empty_group_title": "ไม่พบสินทรัพย์ในกลุ่ม {group}",
        "dashboard.empty_group_subtitle": "กลุ่มที่เลือกยังไม่มีรายการสินทรัพย์",
        "dashboard.empty_group_cta": "เปลี่ยนตัวกรองหรือแก้ไขกลุ่มสินทรัพย์",
        "dashboard.price_feed_warning": "ราคาแบบเรียลไทม์ล่าช้าสำหรับ {count} รายการ จึงใช้ต้นทุนเฉลี่ยชั่วคราว{suffix}",
        "dashboard.sort.az": "A-Z",
        "dashboard.sort.profit": "กำไร",
        "dashboard.sort.value": "มูลค่า",
        "trade_plan.title": "PRO TRADE PLAN BUILDER",
        "trade_plan.subtitle": "คู่มือเชิง Heuristic สำหรับตัดสินใจรายตัว",
        "trade_plan.legend": (
            "หมายเหตุ: Profit=%กำไร/ขาดทุนเทียบต้นทุน, Entry=โซนเข้า, TP1/TP2=จุดทำกำไร, "
            "SL=จุดตัดขาดทุน, R:R=ผลตอบแทนต่อความเสี่ยง, PosRisk=%ความเสี่ยงต่อไม้"
        ),
        "trade_plan.preview": "ตัวอย่างสำหรับ PRO",
        "trade_plan.unlock": "ปลดล็อกแผนเทรดเต็มรูปแบบ",
        "trade_plan.no_preview": "ยังไม่มีสินทรัพย์สำหรับแสดงตัวอย่าง",
        "trade_plan.create_alert": "สร้างแจ้งเตือน",
        "trade_plan.view_chart": "ดูกราฟ",
        "health.title": "PORTFOLIO HEALTH SCORE",
        "health.top_issues": "ประเด็นหลัก",
        "health.action_plan": "แผนปรับพอร์ต",
        "health.what_if": "คะแนนหลังปรับตามแผน: {score}/100",
        "health.uplift": "โอกาสเพิ่มคะแนน: +{delta}",
        "health.mode": "โหมด: Balanced Retail",
        "health.no_holdings": "ยังไม่มีสินทรัพย์ในพอร์ต",
        "health.no_holdings_action": "เพิ่มสินทรัพย์เพื่อให้ระบบประเมินสุขภาพพอร์ต",
        "health.zero_value": "มูลค่าพอร์ตเป็นศูนย์",
        "health.zero_value_action": "กรุณาอัปเดตราคา/จำนวนหุ้นก่อนประเมิน",
        "health.balanced": "โครงสร้างพอร์ตสมดุลและความเสี่ยงอยู่ในระดับที่จัดการได้",
        "health.balanced_action": "รักษาวินัยการจัดสรรและทบทวนความเสี่ยงรายสัปดาห์",
        "health.issue.concentration": "ความเสี่ยงกระจุกตัว: อันดับ 1 มีสัดส่วน {value:.1f}% ของพอร์ต",
        "health.issue.drawdown": "แรงกดดันฝั่งขาดทุน: {value:.1f}% ของพอร์ตอยู่ในสถานะติดลบ",
        "health.issue.volatility": "ความผันผวนฝั่งขาลงของพอร์ตยังสูง",
        "health.issue.correlation": "ความเสี่ยงจากความสัมพันธ์สูง: 3 อันดับแรกคิดเป็น {value:.1f}%",
        "health.action.concentration": "ลดสัดส่วนตัวใหญ่เกินไปและกระจายไปสินทรัพย์ที่ไม่วิ่งทิศเดียวกัน",
        "health.action.drawdown": "ตั้ง stop-loss ให้ชัดและลดน้ำหนักสินทรัพย์ที่อ่อนแรงต่อเนื่อง",
        "health.action.volatility": "ลดสินทรัพย์เบตาสูงและเพิ่มสินทรัพย์ผันผวนต่ำ",
        "health.action.correlation": "กระจายข้ามธีม/ข้ามอุตสาหกรรมเพื่อลดแรงกระแทกพร้อมกัน",
        "health.sub.concentration": "กระจุกตัว",
        "health.sub.drawdown": "ขาดทุนสะสม",
        "health.sub.volatility": "ผันผวน",
        "health.sub.correlation": "สัมพันธ์กันสูง",
        "health.penalty.breakdown": "รายละเอียดการหักคะแนน",
        "health.issue_prefix": "ปัญหา:",
        "health.action_prefix": "แผนแก้:",
        "health.unlock_full": "ปลดล็อกการวิเคราะห์สุขภาพพอร์ตแบบเต็ม",
        "health.teaser_issue": "การวิเคราะห์ความเสี่ยงเต็มรูปแบบมีใน PRO",
        "health.teaser_action": "อัปเกรด PRO เพื่อดูแผนแก้แบบละเอียด",
        "table.empty.title": "ไม่พบสินทรัพย์",
        "table.empty.subtitle": "กด + เพิ่มสินทรัพย์ เพื่อเริ่มใช้งาน",
        "table.lock.ai": "อัปเกรดเป็น PRO เพื่อปลดล็อก AI วิเคราะห์หุ้นรายตัว",
        "table.meta.price": "ราคา",
        "table.meta.avg": "เฉลี่ย",
        "table.meta.hold": "ถือ",
        "charts.locked_timeframe": "ช่วงเวลา 1W/1M ใช้ได้สำหรับ VIP/PRO เท่านั้น",
        "charts.data_feed_unavailable": "ไม่พบข้อมูลราคา {ticker} ({interval}) ในขณะนี้ โปรดลองช่วงเวลาอื่นหรือรอสักครู่",
        "charts.data_feed_unavailable_short": "ไม่พบข้อมูลจาก Data Feed\nกรุณาลองใหม่อีกครั้ง",
        "charts.load_failed": "โหลดกราฟ {ticker} ({interval}) ไม่สำเร็จ",
        "router.feature_locked": "ฟีเจอร์ {feature} ใช้ได้สำหรับ PRO เท่านั้น",
        "router.main_menu": "เมนูหลัก",
        "router.pro_tools": "เครื่องมือ PRO",
        "router.menu.dashboard": "แดชบอร์ด",
        "router.menu.analytics": "วิเคราะห์พอร์ต",
        "router.menu.matchmaker": "AI Matchmaker",
        "router.menu.dividend": "ปันผล",
        "router.menu.heatmap": "ฮีทแมพ",
        "router.menu.simulator": "จำลองหุ้น 2 ตัว",
        "router.menu.alerts": "แจ้งเตือนราคา",
        "router.menu.export": "ส่งออกข้อมูล",
        "router.menu.upgrade": "อัปเกรด PRO",
        "router.market_pulse": "ชีพจรตลาด",
        "router.loading": "กำลังโหลด",
        "router.updated_initial": "อัปเดต ...",
        "router.updated_age": "อัปเดต {age}",
        "router.macro_hud": "Macro HUD",
        "router.main_site": "เว็บไซต์หลัก",
        "copilot.title": "APEXIFY COPILOT",
        "copilot.fab": "Apexify Copilot",
        "copilot.placeholder": 'ถาม AI ได้เลย เช่น "วิเคราะห์ TSLA แบบสั้น"',
        "copilot.upgrade_body": "**Copilot เป็นฟีเจอร์สำหรับ PRO/VIP**\n\nอัปเกรดเพื่อใช้งาน AI บนเว็บแบบเต็ม",
        "copilot.upgrade_btn": "อัปเกรดเป็น PRO",
        "copilot.thinking": "Copilot กำลังคิด...",
        "copilot.send": "ส่ง",
        "copilot.open_gemini": "เปิดหน้า Gemini",
        "auth.login_success": "เข้าสู่ระบบสำเร็จ",
        "auth.token_disabled": "ปิดการเข้าสู่ระบบด้วยโทเคน",
    },
}


_PHRASE_PAIRS: list[tuple[str, str]] = [
    ("MAIN MENU", "เมนูหลัก"),
    ("PRO TOOLS", "เครื่องมือ PRO"),
    ("Dashboard", "แดชบอร์ด"),
    ("Analytics", "วิเคราะห์พอร์ต"),
    ("AI Matchmaker", "AI Matchmaker"),
    ("Dividend", "ปันผล"),
    ("Heatmap", "ฮีทแมพ"),
    ("2-Stock Simulator", "จำลองหุ้น 2 ตัว"),
    ("Price Alerts", "แจ้งเตือนราคา"),
    ("Export", "ส่งออกข้อมูล"),
    ("Upgrade PRO", "อัปเกรด PRO"),
    ("MARKET PULSE", "ชีพจรตลาด"),
    ("Loading", "กำลังโหลด"),
    ("Updated ...", "อัปเดต ..."),
    ("Macro HUD", "Macro HUD"),
    ("APEXIFY COPILOT", "APEXIFY COPILOT"),
    ("Apexify Copilot", "Apexify Copilot"),
    ("UPGRADE TO PRO", "อัปเกรดเป็น PRO"),
    ("UNLOCKED", "ปลดล็อกแล้ว"),
    ("PRO FEATURE", "ฟีเจอร์ PRO"),
    ("UNLOCK FULL TRADE PLAN", "ปลดล็อกแผนเทรดเต็มรูปแบบ"),
    ("No holdings available for preview.", "ยังไม่มีสินทรัพย์สำหรับแสดงตัวอย่าง"),
    ("Risk diagnosis available in PRO", "การวิเคราะห์ความเสี่ยงเต็มรูปแบบมีใน PRO"),
    ("Unlock PRO for full action plan", "อัปเกรด PRO เพื่อดูแผนแก้แบบละเอียด"),
    ("UNLOCK FULL HEALTH DIAGNOSIS", "ปลดล็อกการวิเคราะห์สุขภาพพอร์ตแบบเต็ม"),
    ("Create Alert", "สร้างแจ้งเตือน"),
    ("View Chart", "ดูกราฟ"),
    ("Login success", "เข้าสู่ระบบสำเร็จ"),
    ("Token login is disabled.", "ปิดการเข้าสู่ระบบด้วยโทเคน"),
    ("ACTIVE", "กำลังใช้งาน"),
    ("TRIGGERED", "ทริกแล้ว"),
    ("Issue:", "ปัญหา:"),
    ("Action:", "แผนแก้:"),
    ("Valid till:", "ใช้งานได้ถึง:"),
]


_DYNAMIC_PATTERNS: list[tuple[re.Pattern[str], Callable[[re.Match[str], str], str]]] = [
    (
        re.compile(r"^Valid till:\s*(.+)$", re.IGNORECASE),
        lambda m, lang: tr("dashboard.status.valid_till", lang, date=m.group(1).strip()),
    ),
    (
        re.compile(r"^What-if score after fixes:\s*(\d+)/100$", re.IGNORECASE),
        lambda m, lang: tr("health.what_if", lang, score=m.group(1)),
    ),
    (
        re.compile(r"^Score\s*(\d+)/100$", re.IGNORECASE),
        lambda m, lang: ("คะแนน " if normalize_lang(lang) == "TH" else "Score ") + f"{m.group(1)}/100",
    ),
]


_PHRASE_LOOKUP: dict[str, dict[str, str]] = {}
for en_text, th_text in _PHRASE_PAIRS:
    _PHRASE_LOOKUP[en_text] = {"EN": en_text, "TH": th_text}
    _PHRASE_LOOKUP[th_text] = {"EN": en_text, "TH": th_text}


def tr(key: str, lang: str | None = "TH", **kwargs: Any) -> str:
    target_lang = normalize_lang(lang)
    template = (
        _TRANSLATIONS.get(target_lang, {}).get(key)
        or _TRANSLATIONS["EN"].get(key)
        or key
    )
    template = _repair_mojibake(template)
    try:
        return template.format(**kwargs)
    except Exception:
        return template


def _looks_mojibake(text: str) -> bool:
    if not isinstance(text, str):
        return False
    if any("\u0080" <= ch <= "\u009f" for ch in text):
        return True
    # Common mojibake prefixes from Thai UTF-8 decoded with the wrong codec.
    return any(token in text for token in ("เธ", "เน", "โ€", "ย€"))


def _decode_chain(value: str, encodings: tuple[str, ...]) -> str:
    candidate = value
    for source_encoding in encodings:
        try:
            raw = candidate.encode(source_encoding)
            decoded = raw.decode("utf-8")
            candidate = decoded
        except Exception:
            continue
    return candidate


def _repair_mojibake(text: str) -> str:
    repaired = str(text)

    for _ in range(2):
        if not _looks_mojibake(repaired):
            break
        next_value = _decode_chain(repaired, ("cp874", "latin-1", "cp1252"))
        if next_value == repaired:
            break
        repaired = next_value

    repaired = repaired.replace("โ€ข", "•")
    repaired = repaired.replace("โ\u0002", "•")
    repaired = repaired.replace("??", "")
    repaired = re.sub(r"\s{2,}", " ", repaired)
    return repaired.strip()


def translate_text(text: str, lang: str | None = "TH") -> str:
    if not isinstance(text, str):
        return text

    cleaned = _repair_mojibake(text)
    target_lang = normalize_lang(lang)

    for pattern, handler in _DYNAMIC_PATTERNS:
        match = pattern.match(cleaned)
        if match:
            return _repair_mojibake(handler(match, target_lang))

    phrase = _PHRASE_LOOKUP.get(cleaned)
    if phrase:
        return _repair_mojibake(phrase.get(target_lang, cleaned))

    return cleaned


def install_ui_text_i18n(ui_obj: Any, lang_getter: Callable[[], str]) -> None:
    if getattr(ui_obj, "_apx_i18n_installed", False):
        return

    def _current_lang() -> str:
        try:
            return normalize_lang(lang_getter())
        except Exception:
            return "TH"

    def _translate(value: Any) -> Any:
        if isinstance(value, str):
            return translate_text(value, _current_lang())
        return value

    original_label = ui_obj.label
    original_button = ui_obj.button
    original_notify = ui_obj.notify
    original_markdown = ui_obj.markdown
    original_input = ui_obj.input
    original_textarea = ui_obj.textarea
    original_select = ui_obj.select

    def label(text: Any = "", *args: Any, **kwargs: Any) -> Any:
        return original_label(_translate(text), *args, **kwargs)

    def button(*args: Any, **kwargs: Any) -> Any:
        mutable_args = list(args)
        if mutable_args and isinstance(mutable_args[0], str):
            mutable_args[0] = _translate(mutable_args[0])
        if isinstance(kwargs.get("text"), str):
            kwargs["text"] = _translate(kwargs["text"])
        return original_button(*mutable_args, **kwargs)

    def notify(message: Any = None, *args: Any, **kwargs: Any) -> Any:
        return original_notify(_translate(message), *args, **kwargs)

    def markdown(content: Any = "", *args: Any, **kwargs: Any) -> Any:
        return original_markdown(_translate(content), *args, **kwargs)

    def input_field(*args: Any, **kwargs: Any) -> Any:
        mutable_args = list(args)
        if mutable_args and isinstance(mutable_args[0], str):
            mutable_args[0] = _translate(mutable_args[0])
        if isinstance(kwargs.get("label"), str):
            kwargs["label"] = _translate(kwargs["label"])
        if isinstance(kwargs.get("placeholder"), str):
            kwargs["placeholder"] = _translate(kwargs["placeholder"])
        return original_input(*mutable_args, **kwargs)

    def textarea_field(*args: Any, **kwargs: Any) -> Any:
        mutable_args = list(args)
        if mutable_args and isinstance(mutable_args[0], str):
            mutable_args[0] = _translate(mutable_args[0])
        if isinstance(kwargs.get("label"), str):
            kwargs["label"] = _translate(kwargs["label"])
        if isinstance(kwargs.get("placeholder"), str):
            kwargs["placeholder"] = _translate(kwargs["placeholder"])
        return original_textarea(*mutable_args, **kwargs)

    def select_field(*args: Any, **kwargs: Any) -> Any:
        if isinstance(kwargs.get("label"), str):
            kwargs["label"] = _translate(kwargs["label"])
        return original_select(*args, **kwargs)

    ui_obj.label = label
    ui_obj.button = button
    ui_obj.notify = notify
    ui_obj.markdown = markdown
    ui_obj.input = input_field
    ui_obj.textarea = textarea_field
    ui_obj.select = select_field
    ui_obj._apx_i18n_installed = True
