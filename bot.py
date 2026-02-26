from telegram.handlers import bot, register_handlers

if __name__ == "__main__":
    print("🤖 กำลังเชื่อมต่อ Telegram Bot...")
    try:
        register_handlers()
        print("✅ บอท Apex Wealth Master ออนไลน์แล้ว!")
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ ไม่สามารถเริ่มบอทได้: {e}")