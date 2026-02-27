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
    คุณคือนักวิเคราะห์หุ้นระดับสถาบัน (Apex Wealth Master)
    โปรดวิเคราะห์หุ้น {symbol} จากข้อมูลทางเทคนิคต่อไปนี้:
    - ราคาปัจจุบัน: {price}
    - RSI (14): {rsi:.2f}
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

def analyze_payment_slip(image_bytes) -> str:
    """ให้ AI อ่านและสกัดข้อมูลจากภาพสลิปโอนเงิน"""
    if not ai_client:
        return '{"is_slip": false, "error": "AI not configured"}'
        
    prompt = """
    ตรวจสอบภาพนี้ว่าเป็นสลิปโอนเงินธนาคารของไทยหรือไม่
    ถ้าใช่ ให้ดึงข้อมูล 'ยอดเงิน (amount)' และ 'เลขที่อ้างอิง (ref_no)' ออกมา
    ตอบกลับมาเป็น JSON format เท่านั้น ห้ามมีข้อความอื่นปน
    ตัวอย่าง: {"is_slip": true, "amount": 499.00, "ref_no": "0123456789ABCDEF"}
    ถ้าไม่ใช่สลิปโอนเงิน ให้ตอบ: {"is_slip": false}
    """
    
    try:
        # สมมติว่า image_bytes คือ data ที่อ่านมาจากไฟล์หรือบอท
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, image_bytes]
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"AI Slip Analysis Error: {e}")
        return '{"is_slip": false}'
