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

    bad_tokens = ("\u0E40\u0E19\u20AC\u0E40\u0E18", "\u0E42\u20AC", "\u0E22\u20AC", "\u00C3", "\u00C2", "\ufffd")
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
    should_attempt_repair = _looks_unreadable(raw) or any(
        token in raw for token in ("\u0E40\u0E19\u20AC\u0E40\u0E18", "\u0E42\u20AC", "\u0E22\u20AC", "\u00C3", "\u00C2", "\ufffd")
    )
    if should_attempt_repair:
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
        model="gemini-3-flash-preview",
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


def _generate_matchmaker_batch(exclude_tickers: set[str], batch_size: int = 30, style: str = "mixed") -> list[dict]:
    """Generate one batch of stock recommendations."""
    import random

    exclude_desc = ", ".join(sorted(exclude_tickers)) if exclude_tickers else "none"
    seed = f"{random.choice(['alpha','bravo','charlie','delta','echo','foxtrot','golf','hotel','india','juliet','kilo','lima','mike','november','oscar','papa','quebec','romeo','sierra','tango'])}-{random.randint(1000,9999)}"

    style_hints = {
        "mixed": "Mix large-cap blue chips, growth stocks, dividend plays, hidden gems, REITs, ETFs, and international ADRs.",
        "growth": "Focus on growth stocks: tech, biotech, fintech, AI, cloud, EV, clean energy. Include mid-caps and small-caps.",
        "dividend": "Focus on dividend stocks: utilities, REITs, consumer staples, telecoms, banks. Yield > 2% preferred.",
        "value": "Focus on value/hidden gems: undervalued mid-caps, international ADRs, niche sectors, turnaround plays.",
    }

    prompt = f"""
You are an AI stock matchmaker for Apexify investment platform. Seed: {seed}

Generate exactly {batch_size} diverse stock recommendations for investors.
DO NOT include any of these tickers: {exclude_desc}

Style: {style_hints.get(style, style_hints['mixed'])}

Return ONLY a valid JSON array. No markdown, no extra text.
Each item must have exactly these fields:
[
  {{"ticker": "AAPL", "name": "Apple Inc", "reason": "short reason in Thai", "sector": "Technology", "match_score": 90}}
]

Rules:
- match_score: 60-99 (vary realistically)
- reason: 1 sentence in Thai explaining investment appeal
- Cover many different sectors
- Be creative — include unexpected/lesser-known picks
- All tickers must be valid US-listed symbols
- Do NOT repeat any ticker in the list
"""
    try:
        text = _generate_text(prompt)
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        recs = json.loads(cleaned)
        if isinstance(recs, list):
            return [r for r in recs if r.get("ticker", "").upper() not in exclude_tickers]
        return []
    except Exception as e:
        logger.error(f"Matchmaker batch AI error: {e}")
        return []


def generate_matchmaker_pool(exclude_tickers: set[str] | None = None) -> list[dict]:
    """Generate a shared pool of ~100 diverse stock recommendations (4 batches of 25)."""
    if not ai_client:
        return []

    import random

    exclude = set(exclude_tickers or set())
    all_recs: list[dict] = []
    seen_tickers: set[str] = set(exclude)

    # Generate 4 batches with different styles to get ~100 unique stocks
    for style in ["mixed", "growth", "dividend", "value"]:
        batch = _generate_matchmaker_batch(seen_tickers, batch_size=25, style=style)
        for rec in batch:
            ticker = rec.get("ticker", "").upper()
            if ticker and ticker not in seen_tickers:
                all_recs.append(rec)
                seen_tickers.add(ticker)

    random.shuffle(all_recs)
    logger.info(f"Matchmaker pool generated: {len(all_recs)} stocks")
    return all_recs


def generate_morning_briefing(market_summary: str) -> str:
    """Generate AI morning briefing for PRO users."""
    if not ai_client:
        return "AI system is unavailable (missing API key)."

    prompt = f"""
You are Apexify Morning Briefing AI.
Create a concise daily market briefing based on this data:
{market_summary}

Output as Markdown with these sections:

## 🌅 สรุปตลาดวันนี้
2-3 sentences about overall market sentiment and key moves.

## 📊 จุดสำคัญ
3-5 bullet points with key observations (indices, sectors, commodities).

## ⚠️ สิ่งที่ต้องระวัง
2-3 risk factors or events to watch today.

## 💡 คำแนะนำวันนี้
2-3 actionable suggestions for the day.

Rules:
- Thai first, practical, risk-first, concise
- Use emojis for visual scanning
- No return guarantees
- Keep under 300 words
"""
    try:
        text = _generate_text(prompt)
        fallback = (
            "## 🌅 สรุปตลาดวันนี้\n"
            "ไม่สามารถสร้างสรุปได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง\n"
        )
        return _normalize_ai_text(text, fallback)
    except Exception as e:
        logger.error(f"Morning briefing AI error: {e}")
        return f"Morning briefing error: {e}"


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
            model="gemini-3-flash-preview",
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

Output must be Markdown only with these sections:

## 📊 วิเคราะห์ภาพรวม
Short diagnosis (2-4 lines) about overall portfolio health.

## 📋 แผนปรับสมดุล
Table columns exactly:
| 📌 สินทรัพย์ | ⚖️ สัดส่วนปัจจุบัน | 🎯 เป้าหมาย | ⚡ Action | 💡 เหตุผล |

Use emoji for Action column:
- 🟢 Buy = ซื้อเพิ่ม
- 🟡 Hold = ถือต่อ
- 🔴 Reduce = ลดสัดส่วน

## ✅ สิ่งที่ควรทำ
2-4 actionable bullet points with emoji prefixes.

Use Thai language. Keep concise, practical, risk-first.
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
