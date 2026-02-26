from supabase import create_client, Client
from core.config import SUPABASE_URL, SUPABASE_KEY

def get_db_client() -> Client:
    """สร้างและส่งคืนตัวเชื่อมต่อฐานข้อมูล Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  คำเตือน: ไม่พบ SUPABASE_URL หรือ SUPABASE_KEY ในไฟล์ .env")
        print("กรุณาใส่ข้อมูลให้ครบถ้วนเพื่อเชื่อมต่อฐานข้อมูล")
        
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ Supabase: {e}")
        return None

# สร้างตัวแปรกลางไว้ให้ไฟล์อื่นเรียกใช้งาน (เช่น db.table('users').select('*'))
db = get_db_client()