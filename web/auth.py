import logging
from datetime import UTC, datetime, timedelta
from hmac import compare_digest

import jwt
from nicegui import app, ui
from jwt import ExpiredSignatureError, InvalidTokenError

from core.config import (
    AUTH_ALLOW_TOKEN_LOGIN,
    AUTH_LOCK_MINUTES,
    AUTH_MAX_ATTEMPTS,
    AUTH_MODE,
    AUTH_SESSION_MINUTES,
    AUTH_SHARED_PASSCODE,
    DASHBOARD_LOGIN_SECRET,
)
from core.models import get_user_by_telegram

logger = logging.getLogger(__name__)
_last_token_login_error = "invalid"


def _get_failed_attempts() -> int:
    return int(app.storage.user.get("failed_attempts", 0))


def _is_locked() -> bool:
    lock_until = app.storage.user.get("auth_lock_until")
    if not lock_until:
        return False
    try:
        return datetime.now(UTC) < datetime.fromisoformat(lock_until)
    except ValueError:
        return False


def _record_failed_attempt() -> None:
    failed = _get_failed_attempts() + 1
    app.storage.user["failed_attempts"] = failed
    if failed >= AUTH_MAX_ATTEMPTS:
        lock_until = datetime.now(UTC) + timedelta(minutes=AUTH_LOCK_MINUTES)
        app.storage.user["auth_lock_until"] = lock_until.isoformat()


def _reset_attempt_state() -> None:
    app.storage.user["failed_attempts"] = 0
    app.storage.user.pop("auth_lock_until", None)


def _verify_password(tid_str: str, password: str) -> bool:
    if AUTH_MODE == "shared_passcode":
        return bool(AUTH_SHARED_PASSCODE) and compare_digest(password, AUTH_SHARED_PASSCODE)
    if AUTH_MODE == "legacy_pin":
        return password == tid_str[-4:]
    return False


def _password_hint() -> str:
    if AUTH_MODE == "shared_passcode":
        return "Use the secure passcode from admin."
    if AUTH_MODE == "legacy_pin":
        return "Legacy mode: password = last 4 digits of Telegram ID."
    return "Auth mode is not configured."


def _mask_telegram_id(tid: str) -> str:
    raw = str(tid or "").strip()
    if len(raw) <= 4:
        return "****"
    return f"{raw[:2]}***{raw[-2:]}"


def get_token_login_error() -> str:
    return _last_token_login_error


def _verify_dashboard_token(token: str) -> dict | None:
    global _last_token_login_error
    _last_token_login_error = "invalid"

    if not AUTH_ALLOW_TOKEN_LOGIN:
        _last_token_login_error = "disabled"
        return None
    if not DASHBOARD_LOGIN_SECRET:
        _last_token_login_error = "misconfigured"
        return None

    raw_token = (token or "").strip()
    if not raw_token:
        return None

    try:
        payload = jwt.decode(
            raw_token,
            DASHBOARD_LOGIN_SECRET,
            algorithms=["HS256"],
            options={"require": ["exp"]},
        )
    except ExpiredSignatureError:
        _last_token_login_error = "expired"
        return None
    except InvalidTokenError:
        _last_token_login_error = "invalid"
        return None

    tid = payload.get("telegram_id") or payload.get("tid")
    if tid is None:
        _last_token_login_error = "invalid"
        return None

    tid_str = str(tid).strip()
    if not tid_str:
        _last_token_login_error = "invalid"
        return None

    _last_token_login_error = "ok"
    return {"telegram_id": tid_str}


def _login_user_from_telegram_id(tid: str) -> bool:
    tid_str = str(tid or "").strip()
    if not tid_str:
        return False

    try:
        tid_int = int(tid_str)
    except ValueError:
        return False

    user = get_user_by_telegram(tid_int)
    if not user:
        logger.info("token_login_invalid telegram_id=%s reason=user_not_found", _mask_telegram_id(tid_str))
        return False

    _reset_attempt_state()
    app.storage.user["authenticated"] = True
    app.storage.user["auth_at"] = datetime.now(UTC).isoformat()
    app.storage.user["telegram_id"] = tid_str
    app.storage.user["user_id"] = user["user_id"]

    if "currency" not in app.storage.user:
        app.storage.user["currency"] = "USD"
    if "lang" not in app.storage.user:
        app.storage.user["lang"] = "TH"
    return True


def login_page():
    with ui.column().classes("absolute inset-0 items-center justify-center"):
        ui.element("div").classes(
            "absolute top-10 left-1/2 -translate-x-1/2 w-[560px] h-[560px] rounded-full blur-[120px] bg-[#56D3FF]/16 pointer-events-none"
        )
        with ui.card().classes(
            "w-[94vw] max-w-[430px] p-8 md:p-10 items-center bg-[#0E1822]/92 border border-[#56D3FF]/24 rounded-[28px] shadow-[0_20px_60px_rgba(0,0,0,0.55)] backdrop-blur-xl relative overflow-hidden"
        ):
            ui.element("div").classes(
                "absolute -top-24 -right-24 w-64 h-64 rounded-full blur-3xl bg-[#7EF7CF]/12 pointer-events-none"
            )
            ui.icon("shield_lock", size="3.2rem").classes("text-[#56D3FF] mb-2 z-10")
            ui.label("APEXIFY LOGIN").classes("text-3xl font-black text-white tracking-widest text-center z-10")
            ui.label("Sign in with your Telegram ID").classes("text-gray-400 text-sm mt-1 mb-6 z-10")

            telegram_id_input = ui.input("Telegram ID").classes("w-full mb-3").props("outlined dark")
            password_input = ui.input("Password").classes("w-full mb-2").props("outlined dark password type=password")
            ui.label(_password_hint()).classes("text-[11px] text-amber-300 mb-6 text-center")
            ui.label("เปิดจากปุ่มใน Telegram bot เพื่อ login อัตโนมัติ").classes("text-[11px] text-cyan-300 mb-4 text-center")

            def try_login():
                if _is_locked():
                    ui.notify(
                        f"Too many attempts. Try again in {AUTH_LOCK_MINUTES} minute(s).",
                        type="negative",
                    )
                    return

                try:
                    tid_str = (telegram_id_input.value or "").strip()
                    tid = int(tid_str)
                    pwd = (password_input.value or "").strip()

                    if not _verify_password(tid_str, pwd):
                        _record_failed_attempt()
                        ui.notify("Invalid credentials", type="negative")
                        return

                    user = get_user_by_telegram(tid)
                    if user:
                        _reset_attempt_state()
                        app.storage.user["authenticated"] = True
                        app.storage.user["auth_at"] = datetime.now(UTC).isoformat()
                        app.storage.user["telegram_id"] = str(tid)
                        app.storage.user["user_id"] = user["user_id"]

                        if "currency" not in app.storage.user:
                            app.storage.user["currency"] = "USD"
                        if "lang" not in app.storage.user:
                            app.storage.user["lang"] = "TH"

                        role = user.get("role", "free")
                        role_str = role.upper() if role else "FREE"
                        ui.notify(f"Login success ({role_str})", type="positive")
                        ui.navigate.to("/")
                    else:
                        _record_failed_attempt()
                        ui.notify("Telegram ID not found. Please start bot first.", type="negative")
                except ValueError:
                    _record_failed_attempt()
                    ui.notify("Telegram ID must be numeric", type="negative")

            ui.button("LOGIN", on_click=try_login).classes(
                "w-full bg-gradient-to-r from-[#20D6A1] to-[#39C8FF] text-black font-black rounded-xl py-3 hover:scale-[1.01] transition-transform"
            )


def require_login():
    if not app.storage.user.get("authenticated", False):
        ui.navigate.to("/login")
        return False

    auth_at = app.storage.user.get("auth_at")
    if auth_at:
        try:
            issued_at = datetime.fromisoformat(auth_at)
            if datetime.now(UTC) > issued_at + timedelta(minutes=AUTH_SESSION_MINUTES):
                logout()
                return False
        except ValueError:
            logout()
            return False
    return True


def logout():
    app.storage.user["authenticated"] = False
    app.storage.user.pop("auth_at", None)
    app.storage.user.pop("telegram_id", None)
    app.storage.user.pop("user_id", None)
    ui.navigate.to("/login")
