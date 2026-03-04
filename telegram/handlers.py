import telebot
from urllib.parse import urlencode

from core.config import (
    AUTH_MODE,
    AUTH_SHARED_PASSCODE,
    DASHBOARD_PUBLIC_URL,
    TELEGRAM_TOKEN,
)
from core.database import db
from services.pnl_generator import generate_pnl_card
from services.yahoo_finance import get_live_price
from core.models import get_portfolio
import io
# เริ่มต้นตัวบอท
bot = telebot.TeleBot(TELEGRAM_TOKEN)


def _resolve_dashboard_password(telegram_id: int) -> str:
    mode = str(AUTH_MODE or "").strip().lower()
    if mode == "shared_passcode":
        return str(AUTH_SHARED_PASSCODE or "").strip()
    if mode == "legacy_pin":
        return str(telegram_id)[-4:]
    return ""


def _build_dashboard_link(telegram_id: int) -> str:
    base = str(DASHBOARD_PUBLIC_URL or "").strip().rstrip("/")
    if not base:
        return ""

    query = {"telegram_id": str(telegram_id)}
    password = _resolve_dashboard_password(telegram_id)
    if password:
        query["password"] = password

    return f"{base}/login-token?{urlencode(query)}"


def _dashboard_keyboard(telegram_id: int):
    dashboard_link = _build_dashboard_link(telegram_id)
    if not dashboard_link:
        return None

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("OPEN DASHBOARD", url=dashboard_link))
    return markup


def register_handlers():
    
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        """เมื่อลูกค้าพิมพ์ /start เพื่อเริ่มใช้งาน"""
        telegram_id = message.from_user.id
        # ดึงชื่อ และตัดอักขระ < > ออกเพื่อความปลอดภัยของ HTML Mode
        raw_username = message.from_user.username or message.from_user.first_name
        username = str(raw_username).replace('<', '').replace('>', '')
        
        try:
            # เช็คว่าคนนี้เคยลงทะเบียนในฐานข้อมูลเราหรือยัง
            res = db.table('apex_users').select('*').eq('telegram_id', telegram_id).execute()
            
            if not res.data:
                try:
                    # ถ้ายังไม่เคย ให้สร้าง User ใหม่ลง Supabase
                    db.table('apex_users').insert({
                        'telegram_id': telegram_id,
                        'username': username,
                        'is_vip': False
                    }).execute()
                except Exception as db_err:
                    # ดักจับกรณี Duplicate Key (มีคนกด /start รัวๆ)
                    if '23505' not in str(db_err):
                        raise db_err
                
                # 🌟 เปลี่ยนมาใช้ HTML <b> และ <code> แทน Markdown เพื่อป้องกันบักอักขระพิเศษ
                welcome_text = (
                    f"🚀 ยินดีต้อนรับคุณ <b>{username}</b> สู่ Apex Wealth Master!\n\n"
                    f"วิธีเพิ่มหุ้นเข้าพอร์ต:\n"
                    f"พิมพ์ <code>/add [ชื่อหุ้น] [จำนวน] [ราคาเฉลี่ย]</code>\n"
                    f"ตัวอย่าง: <code>/add NVDA 10.5 450</code>\n\n"
                    f"ระบบจะซิงค์ข้อมูลไปยัง Web Dashboard อัตโนมัติครับ!"
                )
            else:
                welcome_text = f"✅ ยินดีต้อนรับกลับมาครับคุณ <b>{username}</b>! พิมพ์ /add เพื่อเพิ่มหุ้นได้เลย"
                
            # ใช้โหมด HTML ปลอดภัยกับชื่อแปลกๆ
            dashboard_markup = _dashboard_keyboard(telegram_id)
            if dashboard_markup:
                bot.reply_to(message, welcome_text, parse_mode='HTML', reply_markup=dashboard_markup)
            else:
                bot.reply_to(
                    message,
                    f"{welcome_text}\n\n/dashboard (DASHBOARD_PUBLIC_URL is not configured)",
                    parse_mode='HTML',
                )
            
        except Exception as e:
            bot.reply_to(message, f"❌ ระบบฐานข้อมูลมีปัญหา: {e}")

    @bot.message_handler(commands=['dashboard'])
    def open_dashboard(message):
        telegram_id = message.from_user.id
        dashboard_markup = _dashboard_keyboard(telegram_id)

        if not dashboard_markup:
            bot.reply_to(
                message,
                "❌ Dashboard link is not ready yet. Please set DASHBOARD_PUBLIC_URL in environment.",
            )
            return

        bot.reply_to(
            message,
            "🌐 Open dashboard in browser:\n- Tap button below\n- If Telegram opens in-app, choose 'Open in Browser'",
            reply_markup=dashboard_markup,
        )

    @bot.message_handler(commands=['add'])
    def handle_add_stock(message):
        """คำสั่ง /add [ชื่อหุ้น] [จำนวน] [ราคา] [กลุ่ม(Optional)]"""
        try:
            parts = message.text.split()
            # เช็คว่าถ้าใส่มาไม่ครบอย่างน้อย 4 ตัว (คำสั่ง + หุ้น + จำนวน + ราคา)
            if len(parts) < 4:
                bot.reply_to(message, "❌ รูปแบบผิด! กรุณาพิมพ์:\n<code>/add [ชื่อหุ้น] [จำนวน] [ราคา] [กลุ่ม(เช่น DCA, DIV)]</code>\nเช่น: <code>/add AAPL 10 150 DCA</code>", parse_mode='HTML')
                return
            
            ticker = parts[1].upper()
            shares = float(parts[2])
            cost = float(parts[3])
            # ถ้าใส่กรุ๊ปมาให้ใช้ ถ้าไม่ใส่ให้เป็น ALL
            group = parts[4].upper() if len(parts) > 4 else 'ALL'
            
            telegram_id = message.from_user.id
            
            user_res = db.table('apex_users').select('id').eq('telegram_id', telegram_id).execute()
            if not user_res.data:
                bot.reply_to(message, "⚠️ คุณยังไม่ได้ลงทะเบียน กรุณาพิมพ์ /start ก่อนครับ")
                return
            
            db_user_id = user_res.data[0]['id']
            
            # 🌟 บันทึกหุ้นลงพอร์ตพร้อมระบุ Group
            db.table('apex_portfolios').insert({
                'user_id': db_user_id,
                'ticker': ticker,
                'shares': shares,
                'avg_cost': cost,
                'asset_group': group
            }).execute()
            
            bot.reply_to(message, f"✅ เพิ่มหุ้น <b>{ticker}</b> จำนวน {shares} หุ้น (ต้นทุน ${cost})\n📂 จัดอยู่ในกลุ่ม: <b>{group}</b> เรียบร้อยแล้ว!\nเช็คได้ที่หน้าเว็บครับ", parse_mode='HTML')
            
        except ValueError:
            bot.reply_to(message, "❌ จำนวนหุ้นและราคาต้องเป็นตัวเลขเท่านั้นครับ")
        except Exception as e:
            bot.reply_to(message, f"❌ เกิดข้อผิดพลาด: {str(e)}")
    @bot.message_handler(commands=['pnl'])
    def handle_pnl_card(message):
        """คำสั่ง /pnl [ชื่อหุ้น] เพื่อสร้างการ์ดอวดกำไร"""
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ กรุณาพิมพ์ชื่อหุ้นด้วยครับ เช่น <code>/pnl NVDA</code>", parse_mode='HTML')
            return
            
        ticker = parts[1].upper()
        telegram_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        
        # 1. เช็คว่ามีหุ้นนี้ในพอร์ตไหม
        user_res = db.table('apex_users').select('id').eq('telegram_id', telegram_id).execute()
        if not user_res.data:
            bot.reply_to(message, "⚠️ คุณยังไม่ได้ลงทะเบียนครับ พิมพ์ /start ก่อนนะ")
            return
            
        user_id = user_res.data[0]['id']
        portfolio = get_portfolio(user_id)
        asset = next((a for a in portfolio if a['ticker'] == ticker), None)
        
        if not asset:
            bot.reply_to(message, f"❌ ไม่พบหุ้น <b>{ticker}</b> ในพอร์ตของคุณครับ", parse_mode='HTML')
            return
            
        # 2. ส่งข้อความรอ
        wait_msg = bot.reply_to(message, "🎨 กำลังสร้างการ์ด PnL ระดับ Pro ให้คุณ...")
        
        try:
            # 3. ดึงราคาปัจจุบัน และวาดรูป
            entry_price = float(asset['avg_cost'])
            current_price = get_live_price(ticker)
            
            image_bytes = generate_pnl_card(username, ticker, entry_price, current_price)
            
            # 4. ส่งรูปภาพกลับไปให้ผู้ใช้
            bot.send_photo(
                message.chat.id, 
                photo=image_bytes, 
                caption=f"🚀 ผลประกอบการ <b>{ticker}</b> ของคุณ!\nกด Share อวดเพื่อนได้เลย!",
                parse_mode='HTML'
            )
            bot.delete_message(message.chat.id, wait_msg.message_id)
            
        except Exception as e:
            bot.edit_message_text(f"❌ เกิดข้อผิดพลาดในการสร้างภาพ: {e}", message.chat.id, wait_msg.message_id)        
