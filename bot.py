from core.config import TELEGRAM_TOKEN
from telegram.handlers import bot, register_handlers


def run_bot() -> None:
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Missing TELEGRAM_TOKEN")
    register_handlers()
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)


if __name__ == "__main__":
    run_bot()
