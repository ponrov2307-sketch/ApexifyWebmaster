from apscheduler.schedulers.background import BackgroundScheduler
from core.database import db
from services.news_fetcher import fetch_stock_news_summary
from telegram.handlers import bot # ตรวจสอบให้แน่ใจว่า import bot มาจากไฟล์ที่ถูกต้อง

def send_morning_briefing():
    """ฟังก์ชันดึงข่าวและส่งให้ผู้ใช้ระดับ PRO เท่านั้น"""
    try:
        # 🌟 1. ดึงผู้ใช้ที่เป็น PRO (และ Admin) เท่านั้น! ลบ VIP ออก
        users_res = db.table('users').select('id, telegram_id, username').in_('role', ['pro', 'admin']).execute()
        
        for user in users_res.data:
            # ... (โค้ดดึงหุ้นและส่ง Telegram ทำงานตามปกติ)
            user_id = user['id']
            tid = user['telegram_id']
            username = user['username']
            
            # 2. ดึงหุ้นในพอร์ต (เอาแค่ 3 ตัวแรก เพื่อไม่ให้บอทส่งข้อความยาวเกินไป)
            port_res = db.table('portfolios').select('ticker').eq('user_id', user_id).limit(3).execute()
            if not port_res.data:
                continue # ถ้าพอร์ตว่าง ให้ข้ามคนนี้ไป
                
            brief_msg = f"🌅 <b>อรุณสวัสดิ์คุณ {username}!</b>\nนี่คือสรุปข่าวสารหุ้นในพอร์ตของคุณประจำวันนี้ครับ:\n\n"
            
            for item in port_res.data:
                ticker = item['ticker']
                summary = fetch_stock_news_summary(ticker) # ดึงข่าวจาก Gemini
                brief_msg += f"📊 <b>{ticker}</b>:\n{summary}\n\n"
                
            brief_msg += "💡 <i>Apexify AI - ขอให้วันนี้เป็นวันที่กำไรปังๆ ครับ!</i>"
            
            # 3. ส่งข้อความหา User
            bot.send_message(tid, brief_msg, parse_mode='HTML')
            
    except Exception as e:
        print(f"⚠️ Scheduler Error: ไม่สามารถส่ง Morning Briefing ได้ - {e}")

def start_scheduler():
    """เริ่มระบบตั้งเวลา"""
    scheduler = BackgroundScheduler(timezone="Asia/Bangkok")
    # ตั้งเวลาให้ทำงานทุกวันตอน 08:00 น.
    scheduler.add_job(send_morning_briefing, 'cron', hour=8, minute=0)
    scheduler.start()
    print("✅ ระบบ Morning AI Briefing เริ่มทำงานแล้ว (รอส่งตอน 08:00 น.)")