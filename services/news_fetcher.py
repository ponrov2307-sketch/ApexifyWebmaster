import xml.etree.ElementTree as ET
from curl_cffi import requests as cffi_requests
from google import genai
from core.config import GEMINI_API_KEY

def fetch_stock_news_summary(ticker: str) -> str:
    """ดึงข่าวด่วนของหุ้นรายตัว และให้ AI สรุป"""
    try:
        # ตัด .BK ออกเวลาค้นหาข่าวเพื่อความแม่นยำ
        search_term = ticker.replace('.BK', '')
        
        # ดึงข่าวจาก Google News ย้อนหลัง 7 วัน
        url = f"https://news.google.com/rss/search?q={search_term}+stock+OR+หุ้น+when:7d&hl=th&gl=TH&ceid=TH:th"
        res = cffi_requests.get(url, impersonate="chrome110", timeout=10)
        root = ET.fromstring(res.content)
        
        titles = []
        for item in root.findall('.//item')[:5]: # ดึงมาแค่ 5 ข่าวล่าสุดพอ
            title = item.find('title')
            if title is not None:
                titles.append(title.text.strip())
        
        if not titles:
            return f"🔍 **ไม่พบข่าวสารล่าสุด** สำหรับหุ้น {ticker} ในรอบ 7 วันที่ผ่านมาครับ"
            
        titles_str = "\n".join([f"- {t}" for t in titles])
        
        # ส่งให้ Gemini สรุป
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"""
        คุณคือนักวิเคราะห์หุ้นมืออาชีพ 
        นี่คือพาดหัวข่าวล่าสุดของหุ้น {ticker}:
        {titles_str}
        
        ช่วยเขียนสรุปข่าวที่น่าสนใจที่สุด และผลกระทบที่อาจเกิดขึ้นกับหุ้นตัวนี้
        ความยาว 3-4 บรรทัด ด้วยภาษาเป็นกันเอง อ่านง่าย คุยเหมือนเพื่อนเทรดเดอร์ด้วยกัน
        (ถ้าข่าวไหนไม่เกี่ยวเลยให้ข้ามไป)
        """
        
        ai_response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return ai_response.text.strip()
        
    except Exception as e:
        return f"❌ **ขออภัยครับ:** ระบบดึงข่าวมีปัญหาขัดข้องชั่วคราว\n(Error Detail: {e})"
