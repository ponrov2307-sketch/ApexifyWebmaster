import telebot
from core.config import TELEGRAM_TOKEN
from core.database import db

# เริ่มต้นตัวบอท
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def register_handlers():
    
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        """เมื่อลูกค้าพิมพ์ /start เพื่อเริ่มใช้งาน"""
        telegram_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        
        try:
            # เช็คว่าคนนี้เคยลงทะเบียนในฐานข้อมูลเราหรือยัง
            res = db.table('apex_users').select('*').eq('telegram_id', telegram_id).execute()
            
            if not res.data:
                # ถ้ายังไม่เคย ให้สร้าง User ใหม่ลง Supabase
                db.table('apex_users').insert({
                    'telegram_id': telegram_id,
                    'username': username,
                    'is_vip': False
                }).execute()
                
                welcome_text = (
                    f"🚀 ยินดีต้อนรับคุณ {username} สู่ Apex Wealth Master!\n\n"
                    f"วิธีเพิ่มหุ้นเข้าพอร์ต:\n"
                    f"พิมพ์ `/add [ชื่อหุ้น] [จำนวน] [ราคาเฉลี่ย]`\n"
                    f"ตัวอย่าง: `/add NVDA 10.5 450`\n\n"
                    f"ระบบจะซิงค์ข้อมูลไปยัง Web Dashboard อัตโนมัติครับ!"
                )
            else:
                welcome_text = f"✅ ยินดีต้อนรับกลับมาครับคุณ {username}! พิมพ์ /add เพื่อเพิ่มหุ้นได้เลย"
                
            bot.reply_to(message, welcome_text, parse_mode='Markdown')
            
        except Exception as e:
            bot.reply_to(message, f"❌ ระบบฐานข้อมูลมีปัญหา: {e}")

    @bot.message_handler(commands=['add'])
    def add_stock(message):
        """คำสั่งเพิ่มหุ้น เช่น /add AAPL 10 150"""
        try:
            parts = message.text.split()
            # เช็คว่าพิมพ์คำสั่งมาครบไหม (ต้องมี 4 คำ: /add, ชื่อหุ้น, จำนวน, ราคา)
            if len(parts) != 4:
                bot.reply_to(message, "❌ รูปแบบผิด! กรุณาพิมพ์: `/add [ชื่อหุ้น] [จำนวน] [ราคา]`\nเช่น: `/add AAPL 10 150`", parse_mode='Markdown')
                return
            
            ticker = parts[1].upper()
            shares = float(parts[2])
            cost = float(parts[3])
            telegram_id = message.from_user.id
            
            # 1. หา user_id จากฐานข้อมูลก่อน
            user_res = db.table('apex_users').select('id').eq('telegram_id', telegram_id).execute()
            
            if not user_res.data:
                bot.reply_to(message, "⚠️ คุณยังไม่ได้ลงทะเบียน กรุณาพิมพ์ /start ก่อนครับ")
                return
            
            db_user_id = user_res.data[0]['id']
            
            # 2. บันทึกหุ้นลงตาราง portfolios
            db.table('apex_portfolios').insert({
                'user_id': db_user_id,
                'ticker': ticker,
                'shares': shares,
                'avg_cost': cost,
                'asset_group': 'ALL'
            }).execute()
            
            bot.reply_to(message, f"✅ เพิ่มหุ้น **{ticker}** จำนวน {shares} หุ้น (ต้นทุน ${cost}) ลงในพอร์ตเรียบร้อยแล้ว!\nเปิดดูในหน้า Web ได้เลยครับ", parse_mode='Markdown')
            
        except ValueError:
            bot.reply_to(message, "❌ จำนวนหุ้นและราคาต้องเป็นตัวเลขเท่านั้นครับ!")
        except Exception as e:
            bot.reply_to(message, f"❌ เกิดข้อผิดพลาด: {e}")