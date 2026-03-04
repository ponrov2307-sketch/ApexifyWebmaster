from __future__ import annotations

import json
from typing import Any

from google import genai

from core.config import GEMINI_API_KEY
from core.logger import logger


def _build_client() -> genai.Client | None:
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not configured")
        return None
    return genai.Client(api_key=GEMINI_API_KEY)


ai_client = _build_client()


def _count_script(text: str, start: int, end: int) -> int:
    return sum(1 for ch in text if start <= ord(ch) <= end)


def _looks_unreadable(text: str) -> bool:
    if not text:
        return True

    bad_tokens = ("เน€เธ", "เธขโฌ", "โ€", "ย€", "Ã", "Â", "\ufffd")
    bad_score = sum(text.count(token) for token in bad_tokens)
    if bad_score >= 2:
        return True

    thai_count = _count_script(text, 0x0E00, 0x0E7F)
    cyr_count = _count_script(text, 0x0400, 0x04FF)
    cjk_count = _count_script(text, 0x3400, 0x9FFF)
    latin_count = sum(1 for ch in text if ("A" <= ch <= "Z") or ("a" <= ch <= "z"))

    # Suspicious mixed glyph output (typical mojibake from broken webviews)
    if (cyr_count + cjk_count) >= 12 and thai_count == 0 and latin_count < int(len(text) * 0.4):
        return True

    return False


def _normalize_ai_text(text: str, fallback: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return fallback

    cleaned = raw
    try:
        from web.i18n import translate_text  # lazy import to avoid hard coupling

        cleaned = translate_text(raw, "TH")
    except Exception:
        cleaned = raw

    cleaned = cleaned.strip()
    if _looks_unreadable(cleaned):
        return fallback
    return cleaned


def _generate_text(prompt: str) -> str:
    if not ai_client:
        raise RuntimeError("AI service is not configured")
    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return (response.text or "").strip()


def generate_apexify_report(tech_data: dict[str, Any], role: str = "free") -> str:
    """Generate technical analysis summary for one ticker."""
    if not ai_client:
        return "AI system is unavailable (missing API key)."

    symbol = tech_data.get("symbol", "N/A")
    price = tech_data.get("price", 0)
    rsi = tech_data.get("rsi", 0)
    ema20 = tech_data.get("ema20", 0)
    ema50 = tech_data.get("ema50", 0)
    ema200 = tech_data.get("ema200", 0)

    depth = (
        "Provide clear entry/exit idea, stop-loss, and risk notes."
        if role in ["vip", "pro", "admin"]
        else "Provide concise overview only."
    )

    prompt = f"""
You are a professional equity technical analyst.
Analyze ticker {symbol} from this snapshot:
- Current price: {price}
- RSI: {rsi}
- EMA20: {ema20:.2f}
- EMA50: {ema50:.2f}
- EMA200: {ema200:.2f}

Rules:
- Thai first, short English support line if useful
- Risk-first language, no return guarantees
- Keep response practical and scannable
- {depth}
"""
    try:
        text = _generate_text(prompt)
        return _normalize_ai_text(text, "AI analysis temporarily unavailable. Please retry.")
    except Exception as e:
        logger.error(f"AI report error for {symbol}: {e}")
        return f"AI analysis error: {e}"


def generate_copilot_reply(question: str, role: str = "free") -> str:
    """Generic web copilot chat for Apexify."""
    if not ai_client:
        return "AI service is not configured (missing GEMINI_API_KEY)."

    safe_q = (question or "").strip()
    if not safe_q:
        return "Please enter a question."

    prompt = f"""
You are Apexify Copilot, a concise investment assistant.
User role: {str(role).lower()}.
Rules:
- Reply in Thai first, with short English support line when useful.
- Do not promise returns.
- Keep risk-first guidance and practical next steps.
- Keep answer concise and scannable.

User question:
{safe_q}
"""
    try:
        text = _generate_text(prompt)
        return _normalize_ai_text(text, "No response from AI. Please retry.")
    except Exception as e:
        logger.error(f"Copilot AI error: {e}")
        return f"AI error: {e}"


def generate_stock_matchmaker_pitch(ticker: str, price: float, trend_up: bool) -> str:
    """Short AI teaser for stock swipe cards."""
    if not ai_client:
        direction = "แนวโน้มกำลังขึ้น" if trend_up else "แนวโน้มยังแกว่ง"
        return f"{ticker}: {direction} โฟกัสแผนเข้า-ออกและความเสี่ยงก่อนตัดสินใจ"

    prompt = f"""
Write a Thai-first stock pitch in exactly 2 bullet points for ticker {ticker}.
Current price: {price:.2f}
Trend flag: {"uptrend" if trend_up else "sideway/downtrend"}
Rules:
- concise, practical, no hype
- include one risk warning
"""
    try:
        text = _generate_text(prompt)
        fallback = f"{ticker}: ใช้แผนความเสี่ยงก่อนเข้าลงทุน"
        return _normalize_ai_text(text, fallback)
    except Exception as e:
        logger.error(f"Matchmaker AI error for {ticker}: {e}")
        return f"{ticker}: สัญญาณน่าสนใจ แต่ควรตั้งจุด Stop-loss ทุกครั้ง"


def analyze_payment_slip(image_bytes) -> str:
    """Use AI to extract payment slip fields as JSON."""
    if not ai_client:
        return '{"is_slip": false, "error": "AI not configured"}'

    prompt = """
ตรวจสอบภาพนี้ว่าเป็นสลิปโอนเงินของธนาคารไทยหรือไม่
ถ้าใช่ ให้ดึงค่า amount และ ref_no
ตอบเป็น JSON เท่านั้น ไม่มีข้อความอื่น
ตัวอย่าง:
{"is_slip": true, "amount": 499.00, "ref_no": "0123456789xxxx"}
ถ้าไม่ใช่:
{"is_slip": false}
"""
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                prompt,
                {"mime_type": "image/jpeg", "data": image_bytes},
            ],
        )
        text = (response.text or "").strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        return text
    except Exception as e:
        logger.error(f"Slip analysis error: {e}")
        return '{"is_slip": false, "error": "AI processing failed"}'


def generate_rebalance_strategy(portfolio_summary: str) -> str:
    """Generate markdown rebalance strategy table."""
    if not ai_client:
        return "AI system is unavailable (missing API key)."

    prompt = f"""
You are Apexify Portfolio Strategist.
Analyze this portfolio summary and propose a rebalance plan:
{portfolio_summary}

Output must be Markdown only with:
1) Short diagnosis (2-4 lines)
2) Table columns exactly:
| Asset (Ticker) | Current % | Target % | Action | Reason |
3) Short execution notes (2-4 bullets)

Action must be one of: Buy, Hold, Reduce.
Use Thai first. Keep concise and practical. Risk-first.
"""
    try:
        text = _generate_text(prompt)
        fallback = (
            "AI Rebalance result is temporarily unavailable.\n\n"
            "| Asset (Ticker) | Current % | Target % | Action | Reason |\n"
            "|---|---:|---:|---|---|\n"
            "| N/A | - | - | Hold | Retry when data feed is stable. |"
        )
        return _normalize_ai_text(text, fallback)
    except Exception as e:
        logger.error(f"Rebalance AI error: {e}")
        return f"AI Rebalance error: {e}"


def generate_port_doctor_diagnosis(portfolio_summary: str) -> str:
    """Generate doctor-style portfolio diagnosis."""
    if not ai_client:
        return "AI system is unavailable (missing API key)."

    prompt = f"""
You are "Portfolio Doctor" for Apexify.
Diagnose this portfolio:
{portfolio_summary}

Output as Markdown with sections:
1) Overall health score (0-100) + 1 short summary
2) Key risk findings (2-4 bullets)
3) Prescriptions / action plan (2-4 bullets)

Style: Thai first, practical, risk-first, concise.
"""
    try:
        text = _generate_text(prompt)
        fallback = (
            "### Portfolio Doctor\n"
            "- Health score: N/A\n"
            "- Unable to generate diagnosis now.\n"
            "- Please retry in a few minutes."
        )
        return _normalize_ai_text(text, fallback)
    except Exception as e:
        logger.error(f"Port Doctor AI error: {e}")
        return f"Port Doctor AI error: {e}"
