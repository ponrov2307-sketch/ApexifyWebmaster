from core.database import db
from core.models import get_user_by_telegram, get_portfolio
from services.yahoo_finance import get_live_price

def register_portfolio_handlers(bot):
    
    @bot.message_handler(commands=['portfolio', 'port'])
    def show_portfolio(message):
        """คำสั่ง /portfolio เพื่อเช็คพอร์ตผ่านแชท"""
        telegram_id = message.from_user.id
        processing_msg = bot.reply_to(message, "⏳ กำลังดึงข้อมูลพอร์ตและราคาล่าสุด...")
        
        try:
            user = get_user_by_telegram(telegram_id)
            if not user:
                bot.edit_message_text("⚠️ คุณยังไม่ได้ลงทะเบียน กรุณาพิมพ์ /start", chat_id=message.chat.id, message_id=processing_msg.message_id)
                return
            
            portfolio = get_portfolio(user['user_id']) # แก้ตามคีย์ที่ return จาก models.py
            if not portfolio:
                bot.edit_message_text("📊 พอร์ตของคุณยังว่างเปล่า\nพิมพ์ `/add [ชื่อหุ้น] [จำนวน] [ราคา] [กลุ่ม]` เพื่อเพิ่มหุ้นครับ", chat_id=message.chat.id, message_id=processing_msg.message_id, parse_mode='Markdown')
                return
            
            msg = f"📊 **สรุปพอร์ตการลงทุนของคุณ** 📊\n\n"
            total_invested, current_value = 0, 0
            
            for item in portfolio:
                ticker = item['ticker']
                shares = float(item['shares'])
                avg_cost = float(item['avg_cost'])
                group = item.get('asset_group', 'ALL')
                
                live_price = get_live_price(ticker)
                
                invested = shares * avg_cost
                current = shares * live_price
                profit = current - invested
                profit_pct = (profit / invested * 100) if invested > 0 else 0
                
                total_invested += invested
                current_value += current
                
                icon = "🟢" if profit >= 0 else "🔴"
                msg += f"{icon} **{ticker}** `[{group}]`\n"
                msg += f"   • จำนวน: {shares:,.4f} หุ้น\n"
                msg += f"   • ทุนเฉลี่ย: ${avg_cost:,.2f} | ล่าสุด: ${live_price:,.2f}\n"
                msg += f"   • กำไร: ${profit:,.2f} ({profit_pct:+.2f}%)\n\n"
            
            total_profit = current_value - total_invested
            total_profit_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0
            total_icon = "🟢" if total_profit >= 0 else "🔴"
            
            msg += f"====================\n"
            msg += f"💰 **มูลค่าพอร์ตรวม:** ${current_value:,.2f}\n"
            msg += f"💵 **ต้นทุนรวม:** ${total_invested:,.2f}\n"
            msg += f"{total_icon} **กำไรรวม:** ${total_profit:,.2f} ({total_profit_pct:+.2f}%)"
            
            bot.edit_message_text(msg, chat_id=message.chat.id, message_id=processing_msg.message_id, parse_mode='Markdown')
            
        except Exception as e:
            bot.edit_message_text(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูล: {e}", chat_id=message.chat.id, message_id=processing_msg.message_id)