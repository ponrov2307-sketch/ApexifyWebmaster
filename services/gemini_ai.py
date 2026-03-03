import json
from google import genai
from core.config import GEMINI_API_KEY
from core.logger import logger

# ตรวจสอบการตั้งค่า API Key
if GEMINI_API_KEY:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    ai_client = None
    logger.warning("ยังไม่ได้ตั้งค่า GEMINI_API_KEY ใน config.py หรือ .env")

def generate_apexify_report(tech_data: dict, role: str = 'free') -> str:
    """ส่งข้อมูล Technical ให้ Gemini วิเคราะห์และเขียนรายงาน"""
    if not ai_client:
        return "⚠️ ระบบ AI ยังไม่พร้อมใช้งาน (Missing API Key)"
        
    symbol = tech_data.get('symbol', 'N/A')
    price = tech_data.get('price', 0)
    rsi = tech_data.get('rsi', 0)
    ema20 = tech_data.get('ema20', 0)
    ema50 = tech_data.get('ema50', 0)
    ema200 = tech_data.get('ema200', 0)
    
    # ถ้าเป็น VIP/PRO ให้วิเคราะห์ลึกขึ้น
    depth = "วิเคราะห์เจาะลึก พร้อมฟันธงจุดเข้าซื้อ/จุดตัดขาดทุนที่ชัดเจน" if role in ['vip', 'pro'] else "วิเคราะห์ภาพรวมกว้างๆ"

    prompt = f"""
    คุณคือนักวิเคราะห์หุ้นมืออาชีพ
    โปรดวิเคราะห์แนวโน้มของหุ้น {symbol} จากข้อมูลทางเทคนิคต่อไปนี้:
    - ราคาปัจจุบัน: {price}
    - RSI: {rsi}
    - EMA 20: {ema20:.2f}
    - EMA 50: {ema50:.2f}
    - EMA 200: {ema200:.2f}
    
    รูปแบบการตอบ:
    {depth}
    เขียนให้อ่านง่าย เป็นข้อๆ ใช้ภาษาไทยที่เป็นมิตรแต่เป็นมืออาชีพ อิงตามหลักการเทรดจริง
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"AI Report Error for {symbol}: {e}")
        return f"❌ เกิดข้อผิดพลาดในการวิเคราะห์ AI: {e}"

def generate_copilot_reply(question: str, role: str = 'free') -> str:
    """Generic web copilot chat for Apexify."""
    if not ai_client:
        return "AI service is not configured (missing GEMINI_API_KEY)."
    safe_q = (question or '').strip()
    if not safe_q:
        return "Please enter a question."
    prompt = f"""
You are Apexify Copilot, a concise investment assistant.
User role: {str(role).lower()}.
Rules:
- Reply in Thai first, and include short English support line when useful.
- Do not promise returns.
- Keep risk-first guidance and include a brief caution when making suggestions.
- Keep answer practical and scannable.

User question:
{safe_q}
"""
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return (response.text or '').strip() or "No response from AI."
    except Exception as e:
        logger.error(f"Copilot AI Error: {e}")
        return f"AI error: {e}"


def generate_stock_matchmaker_pitch(ticker: str, price: float, trend_up: bool) -> str:
    """Short AI teaser for stock swipe cards."""
    if not ai_client:
        direction = 'แนวโน้มกำลังขึ้น' if trend_up else 'แนวโน้มยังแกว่ง'
        return f'{ticker}: {direction} โฟกัสแผนเข้า-ออกและความเสี่ยงก่อนตัดสินใจ'
    prompt = f"""
Write a short Thai-first stock pitch in 2 bullet points for ticker {ticker}.
Price: {price:.2f}
Trend flag: {"uptrend" if trend_up else "sideway/downtrend"}
Rules:
- concise, practical, no hype
- include one risk warning
"""
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        text = (response.text or '').strip()
        return text or f'{ticker}: ใช้แผนความเสี่ยงก่อนเข้าลงทุน'
    except Exception as e:
        logger.error(f"Matchmaker AI Error for {ticker}: {e}")
        return f'{ticker}: สัญญาณน่าสนใจ แต่ควรตั้งจุด Stop-loss ทุกครั้ง'


def analyze_payment_slip(image_bytes) -> str:
    """ให้ AI อ่านและสกัดข้อมูลจากภาพสลิปโอนเงิน"""
    if not ai_client:
        return '{"is_slip": false, "error": "AI not configured"}'
        
    prompt = """
    ตรวจสอบภาพนี้ว่าเป็นสลิปโอนเงินธนาคารของไทยหรือไม่
    ถ้าใช่ ให้ดึงข้อมูล 'ยอดเงิน (amount)' และ 'เลขที่อ้างอิง (ref_no)' ออกมา
    ตอบกลับมาเป็น JSON format เท่านั้น ห้ามมีข้อความอื่นปน
    ตัวอย่าง: {"is_slip": true, "amount": 499.00, "ref_no": "0123456789xxxx"}
    ถ้าไม่ใช่สลิป ให้ตอบ: {"is_slip": false}
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                prompt,
                {"mime_type": "image/jpeg", "data": image_bytes}
            ]
        )
        
        text = response.text.strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
            
        return text
    except Exception as e:
        logger.error(f"Slip Analysis Error: {e}")
        return '{"is_slip": false, "error": "AI Processing Failed"}'

def generate_rebalance_strategy(portfolio_summary: str) -> str:
    """🌟 ฟังก์ชันให้ Gemini วิเคราะห์และแนะนำตาราง Rebalance พอร์ต"""
    if not ai_client:
        return "⚠️ ระบบ AI ยังไม่พร้อมใช้งาน (Missing API Key)"
        
    prompt = f"""
    คุณคือผู้จัดการกองทุนระดับโลก (AI Hedge Fund Manager) ของ Apexify
    นี่คือข้อมูลพอร์ตการลงทุนปัจจุบันของฉัน (ประกอบด้วยชื่อหุ้น, สัดส่วน %, กำไร/ขาดทุน):
    {portfolio_summary}
    
    จงวิเคราะห์การกระจายความเสี่ยง (Diversification) และแนวโน้มตลาดปัจจุบัน 
    จากนั้นให้คำแนะนำในการ 'ปรับสมดุลพอร์ต (Rebalance)' โดยตอบกลับมาเป็นรูปแบบ "ตาราง Markdown" เท่านั้น! 
    
    โครงสร้างตารางต้องมีคอลัมน์ดังนี้:
    | สินทรัพย์ (Ticker) | สัดส่วนเดิม (%) | สัดส่วนที่แนะนำ (%) | แอคชั่น (Action) | คำแนะนำสั้นๆ |
    
    *ในคอลัมน์ แอคชั่น ให้ใช้คำว่า: 🟢 ซื้อเพิ่ม (Buy), 🔴 ลดพอร์ต (Take Profit/Cut Loss), ⚪️ ถือต่อ (Hold)
    
    ใต้ตาราง ให้เขียนสรุปภาพรวมสั้นๆ 3-4 บรรทัด ว่าทำไมถึงจัดพอร์ตแบบนี้
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Rebalance AI Error: {e}")
        return "⚠️ ขออภัย AI ไม่สามารถประมวลผลกลยุทธ์ได้ในขณะนี้"
def generate_port_doctor_diagnosis(portfolio_summary: str) -> str:
    """🌟 ฟังก์ชันให้ Gemini รับบทเป็นคุณหมอตรวจสุขภาพพอร์ต"""
    if not ai_client:
        return "⚠️ ระบบ AI ยังไม่พร้อมใช้งาน (Missing API Key)"
        
    prompt = f"""
    คุณคือ 'Portfolio Doctor' (คุณหมอตรวจสุขภาพพอร์ตการลงทุนระดับโลก) ของแอป Apexify
    นี่คือข้อมูลพอร์ตการลงทุนปัจจุบันของคนไข้ (ประกอบด้วยชื่อหุ้น, สัดส่วน %, กำไร/ขาดทุน):
    {portfolio_summary}
    
    จงตรวจอาการและวินิจฉัยสุขภาพพอร์ตนี้ โดยตอบกลับในรูปแบบ Markdown ที่อ่านง่ายและน่าสนใจ
    โครงสร้างการตอบ:
    1. 🩺 สรุปสุขภาพรวม: (ให้คะแนนสุขภาพพอร์ตเต็ม 100 พร้อมคำอธิบายสั้นๆ ว่าพอร์ตนี้สุขภาพดีหรือป่วยตรงไหน)
    2. 🦠 อาการที่พบ (ความเสี่ยง): (เช่น กระจุกตัวในหุ้นตัวเดียวมากไป, ถือหุ้นติดลบเยอะเกินไป, หรือถ้าไม่มีปัญหาให้ชมเชย)
    3. 💊 ใบสั่งยา (คำแนะนำ): (แนะนำสั้นๆ ว่าควรทำอย่างไรต่อไป เป็นข้อๆ 2-3 ข้อ)
    
    ใช้ภาษาที่เป็นกันเอง เหมือนหมอใจดีและเชี่ยวชาญ คุยกับคนไข้
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Port Doctor AI Error: {e}")
        return "⚠️ ขออภัย คุณหมอติดคนไข้เคสอื่นอยู่ ไม่สามารถวินิจฉัยอาการได้ในขณะนี้"    
