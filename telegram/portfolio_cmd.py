from core.database import db
from core.models import get_user_by_telegram, get_portfolio
from services.yahoo_finance import get_live_price

def register_portfolio_handlers(bot):
    
    @bot.message_handler(commands=['portfolio', 'port'])
    def show_portfolio(message):
        """คำสั่ง /portfolio เพื่อเช็คพอร์ตผ่านแชท"""
        telegram_id = message.from_user.id
        
        # ส่งข้อความบอกลูกค้าให้รอก่อน (เพราะดึงราคาอาจใช้เวลา 1-2 วินาที)
        processing_msg = bot.reply_to(message, "⏳ กำลังดึงข้อมูลพอร์ตและราคาล่าสุดจากตลาด...")
        
        try:
            # 1. เช็คว่าเป็นสมาชิกหรือยัง
            user = get_user_by_telegram(telegram_id)
            if not user:
                bot.edit_message_text("⚠️ คุณยังไม่ได้ลงทะเบียน กรุณาพิมพ์ /start", chat_id=message.chat.id, message_id=processing_msg.message_id)
                return
            
            # 2. ดึงข้อมูลหุ้นจากฐานข้อมูล
            portfolio = get_portfolio(user['id'])
            if not portfolio:
                bot.edit_message_text("📊 พอร์ตของคุณยังว่างเปล่า\nพิมพ์ `/add [ชื่อหุ้น] [จำนวน] [ราคา]` เพื่อเพิ่มหุ้นครับ", chat_id=message.chat.id, message_id=processing_msg.message_id, parse_mode='Markdown')
                return
            
            # 3. คำนวณมูลค่าและจัดฟอร์แมตข้อความ
            total_invested = 0
            current_value = 0
            
            msg = f"📈 **สรุปพอร์ตของคุณ {user['username']}**\n\n"
            
            for asset in portfolio:
                ticker = asset['ticker']
                shares = float(asset['shares'])
                avg_cost = float(asset['avg_cost'])
                
                # ดึงราคาปัจจุบัน
                live_price = get_live_price(ticker)
                
                invested = shares * avg_cost
                current = shares * live_price
                profit = current - invested
                profit_pct = (profit / invested * 100) if invested > 0 else 0
                
                total_invested += invested
                current_value += current
                
                # ตกแต่งข้อความ
                icon = "🟢" if profit >= 0 else "🔴"
                msg += f"{icon} **{ticker}**\n"
                msg += f"   • จำนวน: {shares:,.4f} หุ้น\n"
                msg += f"   • ทุนเฉลี่ย: ${avg_cost:,.2f} | ล่าสุด: ${live_price:,.2f}\n"
                msg += f"   • กำไร: ${profit:,.2f} ({profit_pct:,.2f}%)\n\n"
            
            # 4. สรุปรวมท้ายบิล
            total_profit = current_value - total_invested
            total_profit_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0
            total_icon = "🟢" if total_profit >= 0 else "🔴"
            
            msg += f"====================\n"
            msg += f"💰 **มูลค่าพอร์ตรวม (Net Worth):** ${current_value:,.2f}\n"
            msg += f"💵 **ต้นทุนรวม (Invested):** ${total_invested:,.2f}\n"
            msg += f"{total_icon} **กำไรรวม (Total Return):** ${total_profit:,.2f} ({total_profit_pct:,.2f}%)\n"
            
            # แก้ไขข้อความที่ให้รอตอนแรก เป็นผลสรุป
            bot.edit_message_text(msg, chat_id=message.chat.id, message_id=processing_msg.message_id, parse_mode='Markdown')
            
        except Exception as e:
            bot.edit_message_text(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูล: {e}", chat_id=message.chat.id, message_id=processing_msg.message_id)