import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)


def _to_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _to_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _require_in_production(name: str, value: str | None) -> None:
    if IS_PRODUCTION and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
IS_PRODUCTION = APP_ENV == "production"

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = _to_int("APP_PORT", 8080)
APP_RELOAD = _to_bool("APP_RELOAD", False)
APP_TITLE = os.getenv("APP_TITLE", "Apex Wealth Master")
NICEGUI_STORAGE_SECRET = os.getenv("NICEGUI_STORAGE_SECRET", "")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
ADMIN_ID = os.getenv("ADMIN_ID", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

AUTH_MODE = os.getenv("AUTH_MODE", "shared_passcode").strip().lower()
AUTH_SHARED_PASSCODE = os.getenv("AUTH_SHARED_PASSCODE", "")
AUTH_MAX_ATTEMPTS = _to_int("AUTH_MAX_ATTEMPTS", 5)
AUTH_LOCK_MINUTES = _to_int("AUTH_LOCK_MINUTES", 15)
AUTH_SESSION_MINUTES = _to_int("AUTH_SESSION_MINUTES", 480)

COLORS = {
    "bg": "#0D1117",
    "card": "#161B22",
    "border": "#30363D",
    "primary": "#D0FD3E",
    "success": "#32D74B",
    "danger": "#FF453A",
    "text_main": "#C9D1D9",
    "text_muted": "#8B949E",
}

MARKET_INDICES = {
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "NASDAQ",
    "^SET.BK": "SET",
    "BTC-USD": "Bitcoin",
    "GC=F": "Gold",
}

_require_in_production("NICEGUI_STORAGE_SECRET", NICEGUI_STORAGE_SECRET)
_require_in_production("DATABASE_URL", DATABASE_URL)
_require_in_production("SUPABASE_URL", SUPABASE_URL)
_require_in_production("SUPABASE_KEY", SUPABASE_KEY)
_require_in_production("TELEGRAM_TOKEN", TELEGRAM_TOKEN)
if AUTH_MODE == "shared_passcode":
    _require_in_production("AUTH_SHARED_PASSCODE", AUTH_SHARED_PASSCODE)
