"""Auth endpoints — login, token-login, me."""

from hmac import compare_digest

import jwt
from fastapi import APIRouter, HTTPException, status
from jwt import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel

from api.deps import CurrentUser, create_session_token
from core.config import (
    AUTH_ALLOW_TOKEN_LOGIN,
    AUTH_MODE,
    AUTH_SHARED_PASSCODE,
    DASHBOARD_LOGIN_SECRET,
)
from core.models import get_user_by_telegram

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------- schemas ----------
class LoginRequest(BaseModel):
    telegram_id: str
    password: str


class TokenLoginRequest(BaseModel):
    token: str


class AuthResponse(BaseModel):
    access_token: str
    user: dict


# ---------- helpers ----------
def _verify_password(tid_str: str, password: str) -> bool:
    if AUTH_MODE == "shared_passcode":
        return bool(AUTH_SHARED_PASSCODE) and compare_digest(password, AUTH_SHARED_PASSCODE)
    if AUTH_MODE == "legacy_pin":
        return password == tid_str[-4:]
    return False


def _verify_dashboard_token(token: str) -> dict | None:
    if not AUTH_ALLOW_TOKEN_LOGIN or not DASHBOARD_LOGIN_SECRET:
        return None
    raw_token = (token or "").strip()
    if not raw_token:
        return None
    try:
        payload = jwt.decode(raw_token, DASHBOARD_LOGIN_SECRET, algorithms=["HS256"], options={"require": ["exp"]})
    except (ExpiredSignatureError, InvalidTokenError):
        return None
    tid = payload.get("telegram_id") or payload.get("tid")
    if tid is None:
        return None
    tid_str = str(tid).strip()
    return {"telegram_id": tid_str} if tid_str else None


def _build_auth_response(user: dict, tid_str: str) -> dict:
    token = create_session_token(user, tid_str)
    return {
        "access_token": token,
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "status": user.get("status", "active"),
            "vip_expiry": user.get("vip_expiry"),
        },
    }


# ---------- endpoints ----------
@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    tid_str = body.telegram_id.strip()
    pwd = body.password.strip()
    if not tid_str or not pwd:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing credentials")

    if not _verify_password(tid_str, pwd):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    try:
        tid_int = int(tid_str)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Telegram ID")

    user = get_user_by_telegram(tid_int)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    return _build_auth_response(user, tid_str)


@router.post("/token-login", response_model=AuthResponse)
async def token_login(body: TokenLoginRequest):
    if not AUTH_ALLOW_TOKEN_LOGIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Token login disabled")

    payload = _verify_dashboard_token(body.token)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    tid_str = payload["telegram_id"]
    try:
        tid_int = int(tid_str)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid telegram_id in token")

    user = get_user_by_telegram(tid_int)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    return _build_auth_response(user, tid_str)


@router.get("/me")
async def me(user: CurrentUser):
    user_info = get_user_by_telegram(int(user.telegram_id))
    if not user_info:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return {
        "user_id": user_info["user_id"],
        "username": user_info["username"],
        "role": user_info["role"],
        "status": user_info.get("status", "active"),
        "vip_expiry": user_info.get("vip_expiry"),
        "telegram_id": user.telegram_id,
    }
