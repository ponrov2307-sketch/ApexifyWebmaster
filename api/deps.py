"""Shared FastAPI dependencies — auth, current user, role checks."""

import warnings
from datetime import UTC, datetime, timedelta
from typing import Annotated

# Suppress JWT InsecureKeyLengthWarning (key length is set via env var)
warnings.filterwarnings("ignore", message=".*HMAC key.*below the minimum.*")

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel

from core.config import (
    AUTH_SESSION_MINUTES,
    DASHBOARD_LOGIN_SECRET,
)
from core.models import get_user_by_telegram


class TokenData(BaseModel):
    telegram_id: str
    user_id: str
    role: str
    username: str
    iat: str  # ISO timestamp


def create_session_token(user: dict, telegram_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "tid": telegram_id,
        "user_id": user["user_id"],
        "role": user["role"],
        "username": user["username"],
        "iat": int(now.timestamp()),
        "exp": now + timedelta(minutes=AUTH_SESSION_MINUTES),
    }
    return jwt.encode(payload, DASHBOARD_LOGIN_SECRET, algorithm="HS256")


def _decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        DASHBOARD_LOGIN_SECRET,
        algorithms=["HS256"],
        options={"require": ["exp"]},
    )


async def get_current_user(
    authorization: Annotated[str, Header()],
) -> TokenData:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing Bearer token")

    raw = authorization[7:]
    try:
        payload = _decode_token(raw)
    except ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    tid = str(payload.get("tid") or payload.get("telegram_id") or "").strip()
    if not tid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload")

    return TokenData(
        telegram_id=tid,
        user_id=str(payload.get("user_id", tid)),
        role=str(payload.get("role", "free")),
        username=str(payload.get("username", "")),
        iat=str(payload.get("iat", "")),
    )


CurrentUser = Annotated[TokenData, Depends(get_current_user)]


def require_role(*roles: str):
    """Dependency that checks the user has one of the given roles."""

    async def _check(user: CurrentUser) -> TokenData:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Upgrade required")
        return user

    return Depends(_check)
