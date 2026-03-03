from datetime import UTC, datetime, timedelta
from hmac import compare_digest

from nicegui import app, ui

from core.config import (
    AUTH_LOCK_MINUTES,
    AUTH_MAX_ATTEMPTS,
    AUTH_MODE,
    AUTH_SESSION_MINUTES,
    AUTH_SHARED_PASSCODE,
)
from core.models import get_user_by_telegram


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
