import logging
from datetime import UTC, datetime, timedelta
from hmac import compare_digest
from pathlib import Path

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


def login_with_dashboard_credentials(telegram_id: str, password: str) -> bool:
    """Fallback login for dashboard links carrying telegram_id + password."""
    tid_str = str(telegram_id or "").strip()
    pwd = str(password or "").strip()
    if not tid_str or not pwd:
        return False
    if not _verify_password(tid_str, pwd):
        return False
    return _login_user_from_telegram_id(tid_str)


def login_page():
    with ui.column().classes("absolute inset-0 items-center justify-center bg-[#080B10]"):
        # Atmospheric glows
        ui.element("div").classes(
            "absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[420px] "
            "rounded-full blur-[140px] bg-[#D0FD3E]/7 pointer-events-none"
        )
        ui.element("div").classes(
            "absolute bottom-0 left-0 w-[450px] h-[450px] "
            "rounded-full blur-[110px] bg-[#00BFFF]/5 pointer-events-none"
        )
        ui.element("div").classes(
            "absolute top-1/3 right-0 w-[350px] h-[350px] "
            "rounded-full blur-[110px] bg-[#AF52DE]/4 pointer-events-none"
        )

        with ui.card().classes(
            "w-[94vw] max-w-[420px] p-0 bg-[#0D1117] rounded-[24px] overflow-hidden relative "
            "shadow-[0_0_0_1px_rgba(208,253,62,0.15),0_50px_100px_rgba(0,0,0,0.8)]"
        ):
            # Top accent line
            ui.element("div").classes(
                "absolute top-0 left-0 right-0 h-[2px] "
                "bg-gradient-to-r from-transparent via-[#D0FD3E]/50 to-transparent"
            )
            # Inner top glow
            ui.element("div").classes(
                "absolute -top-16 left-1/2 -translate-x-1/2 w-[280px] h-[160px] "
                "rounded-full blur-[50px] bg-[#D0FD3E]/8 pointer-events-none"
            )

            with ui.column().classes("w-full p-9 items-center gap-0 relative z-10"):
                # Logo
                _logo_path = Path(__file__).parent.parent / 'static' / 'apexify-logo.png'
                if _logo_path.exists():
                    ui.image("/static/apexify-logo.png").classes(
                        "w-20 h-20 rounded-full object-contain mb-2 "
                        "shadow-[0_0_30px_rgba(208,253,62,0.15)]"
                    )
                else:
                    with ui.element("div").classes(
                        "w-[60px] h-[60px] rounded-2xl flex items-center justify-center mb-4 "
                        "bg-gradient-to-br from-[#D0FD3E]/15 to-[#D0FD3E]/5 "
                        "border border-[#D0FD3E]/25 "
                        "shadow-[0_0_24px_rgba(208,253,62,0.2)]"
                    ):
                        ui.icon("auto_graph", size="2rem").classes("text-[#D0FD3E]")

                ui.label("APEXIFY").classes(
                    "text-[2rem] font-black tracking-[0.35em] text-white leading-none"
                )
                ui.label("PORTFOLIO DASHBOARD").classes(
                    "text-[9px] font-bold tracking-[0.4em] text-[#D0FD3E]/50 mt-1"
                )
                ui.element("div").classes(
                    "w-14 h-px bg-gradient-to-r from-transparent via-[#D0FD3E]/30 to-transparent my-5"
                )
                ui.label("Sign in with your Telegram account").classes(
                    "text-gray-500 text-[13px] mb-5 text-center"
                )

                telegram_id_input = (
                    ui.input("Telegram ID", placeholder="Your Telegram ID number")
                    .classes("w-full mb-3")
                    .props("outlined dark")
                )
                password_input = (
                    ui.input("Password", placeholder="Enter password")
                    .classes("w-full mb-3")
                    .props("outlined dark password type=password")
                )

                with ui.row().classes("w-full justify-between items-start mb-5 flex-wrap gap-1"):
                    ui.label(_password_hint()).classes(
                        "text-[11px] text-[#FCD535]/60 leading-snug max-w-[60%]"
                    )
                    ui.label("หรือเปิดจาก Telegram bot").classes(
                        "text-[11px] text-[#00BFFF]/60 text-right"
                    )

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

                ui.button("SIGN IN", on_click=try_login).props("unelevated").classes(
                    "w-full font-black tracking-[0.2em] text-sm rounded-xl transition-all"
                ).style(
                    "background: #D0FD3E !important; color: #080B10 !important; "
                    "box-shadow: 0 0 20px rgba(208,253,62,0.3); "
                    "letter-spacing: 0.2em;"
                )

                ui.label("APEXIFY © 2025").classes(
                    "text-[10px] text-gray-700 mt-6 tracking-[0.25em]"
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
