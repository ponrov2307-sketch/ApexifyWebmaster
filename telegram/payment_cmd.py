import telebot
import json
from datetime import datetime
from core.database import add_subscription, check_slip_used, mark_slip_used, increment_usage
from services.gemini_ai import analyze_payment_slip
from core.config import ADMIN_ID
from core.logger import logger

def register_payment_handlers(bot: telebot.TeleBot):
    """ลงทะเบียนคำสั่งเกี่ยวกับการชำระเงินและโปรโมชั่น"""

    @bot.message_handler(commands=['redeem'])
    def handle_redeem(message):
        """คำสั่งเติมโค้ดโปรโมชั่น /redeem [CODE]"""
        user_id = str(message.chat.id)
        args = message.text.split()
        
        if len(args) < 2:
            bot.reply_to(message, "❌ รูปแบบคำสั่งไม่ถูกต้อง พิมพ์: `/redeem [โค้ดของคุณ]`", parse_mode="Markdown")
            return
        
        code = args[1].strip().upper()
        # นำเข้า redeem_code จาก database.py ของคุณ
        from core.database import redeem_code
        success, days, expiry, role_type = redeem_code(user_id, code)
        
        if success:
            bot.reply_to(message, f"🎉 **ยินดีด้วย!** เติมโค้ดสำเร็จ\nคุณได้รับการอัปเกรดเป็น **{role_type.upper()} Member** ถึงวันที่: `{expiry}`\n\nสามารถใช้งานฟีเจอร์ใหม่ได้ทันทีครับ 🚀", parse_mode="Markdown")
            increment_usage(user_id)
            logger.info(f"User {user_id} redeemed code: {code}")
        elif days == "already_used_by_you":
            bot.reply_to(message, "⚠️ คุณเคยใช้โค้ดโปรโมชั่นนี้ไปแล้วครับ (1 คน ใช้ได้ 1 ครั้ง)")
        elif days == "fully_used":
            bot.reply_to(message, "❌ น่าเสียดาย! สิทธิ์ของโค้ดนี้ถูกใช้งานครบตามจำนวนแล้วครับ")
        else:
            bot.reply_to(message, "❌ โค้ดไม่ถูกต้อง หรือไม่มีในระบบ")

    @bot.message_handler(content_types=['photo'])
    def handle_payment_slip_check(message):
        """รับภาพสลิปโอนเงินและให้ AI ตรวจสอบ"""
        user_id = str(message.chat.id)
        progress_msg = bot.reply_to(message, "🧾 Apexify กำลังตรวจสอบสลิปโอนเงิน...")
            
        try:
            # ดึงไฟล์ภาพจาก Telegram
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # ส่งภาพให้ Gemini วิเคราะห์
            ai_result = analyze_payment_slip(downloaded_file)
            
            # ทำความสะอาด JSON string ที่ได้จาก AI
            clean_json = ai_result.replace('```json', '').replace('```', '').strip()
            result = json.loads(clean_json)
            
            if result.get('is_slip'):
                amount = float(result.get('amount', 0))
                ref_no = result.get('ref_no', '').strip()
                
                if not ref_no or ref_no.lower() == "none":
                    bot.edit_message_text("⚠️ Apexify อ่าน 'เลขที่อ้างอิง' บนสลิปไม่ชัดเจน โปรดถ่ายให้เห็นชัดๆ ครับ", message.chat.id, progress_msg.message_id)
                    return
                    
                if check_slip_used(ref_no):
                    bot.edit_message_text("❌ **สลิปนี้ถูกใช้งานไปแล้ว!**\nไม่อนุญาตให้ใช้สลิปซ้ำครับ", message.chat.id, progress_msg.message_id, parse_mode="Markdown")
                    bot.send_message(ADMIN_ID, f"🚨 **ทุจริต!** User `{user_id}` ส่งสลิปซ้ำ (Ref: `{ref_no}`)", parse_mode="Markdown")
                    return

                # ตรรกะแยกแพ็กเกจตามยอดเงิน
                if amount == 4990:
                    expiry = add_subscription(user_id, 'pro', 365)
                    msg_text = f"🎉 **ชำระเงินสำเร็จ!** ได้รับสิทธิ์ **👑 PRO (รายปี)**\n⏰ หมดอายุ: {expiry}"
                elif amount == 1990:
                    expiry = add_subscription(user_id, 'vip', 365)
                    msg_text = f"🎉 **ชำระเงินสำเร็จ!** ได้รับสิทธิ์ **💎 VIP (รายปี)**\n⏰ หมดอายุ: {expiry}"
                elif amount == 499:
                    expiry = add_subscription(user_id, 'pro', 30)
                    msg_text = f"🎉 **ชำระเงินสำเร็จ!** ได้รับสิทธิ์ **👑 PRO (รายเดือน)**\n⏰ หมดอายุ: {expiry}"
                elif amount == 199:
                    expiry = add_subscription(user_id, 'vip', 30)
                    msg_text = f"🎉 **ชำระเงินสำเร็จ!** ได้รับสิทธิ์ **💎 VIP (รายเดือน)**\n⏰ หมดอายุ: {expiry}"
                else:
                    bot.edit_message_text(
                        f"❌ **ยอดเงินไม่ตรงกับแพ็กเกจ** ({amount:,.2f} บาท)\nกรุณาโอนให้ตรงราคา (199, 499, 1990, 4990)", 
                        message.chat.id, progress_msg.message_id, parse_mode="Markdown"
                    )
                    return

                # อัปเดตข้อมูลสำเร็จ
                mark_slip_used(ref_no, user_id)
                bot.delete_message(message.chat.id, progress_msg.message_id)
                bot.reply_to(message, msg_text, parse_mode="Markdown")
                bot.send_message(ADMIN_ID, f"💰 เงินเข้า! User `{user_id}` โอน {amount} บาท (แพ็กเกจใหม่)")
                logger.info(f"Payment success: User {user_id} amount {amount}")
                
            else:
                bot.edit_message_text("❌ รูปนี้ไม่ใช่สลิปโอนเงินที่ถูกต้องครับ", message.chat.id, progress_msg.message_id)
                
        except Exception as e:
            logger.error(f"Slip Processing Error: {e}")
            bot.edit_message_text("⚠️ Apexify ขัดข้องในการอ่านสลิป โปรดลองอีกครั้งหรือติดต่อแอดมิน", message.chat.id, progress_msg.message_id)
