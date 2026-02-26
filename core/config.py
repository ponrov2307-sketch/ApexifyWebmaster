import os
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

# ข้อมูลเชื่อมต่อระบบต่างๆ
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ADMIN_ID = os.getenv("ADMIN_ID", "")
# โทนสีหลักของ Apex Wealth Master (ใช้งานร่วมกันทั้งเว็บ)
COLORS = {
    "bg": "#0B0E14",
    "card": "#161B22",
    "accent": "#D0FD3E",      # สีเขียวมะนาว (จุดเด่น)
    "success": "#32D74B",
    "danger": "#FF453A",
    "text_main": "#FFFFFF",
    "text_muted": "#8B949E",   # สีเทาสำหรับตัวหนังสือรอง
    "chart_palette": ["#D0FD3E", "#3B82F6", "#F59E0B", "#EF4444", "#8B5CF6"]
}

# รายชื่อดัชนีตลาดโลกที่ต้องการดึงราคามาโชว์บน Ticker
MARKET_INDICES = {
    "^GSPC": "S&P 500",
    "^IXIC": "NASDAQ",
    "GC=F": "GOLD",
    "THB=X": "USD/THB"
}