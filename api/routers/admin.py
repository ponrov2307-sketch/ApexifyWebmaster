"""Admin-only endpoints."""

import asyncio

from fastapi import APIRouter, HTTPException, status

from api.deps import CurrentUser
from core.models import get_online_users, update_user_last_seen

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/heartbeat")
async def heartbeat(user: CurrentUser):
    """Update last_seen for the current user."""
    await asyncio.to_thread(update_user_last_seen, user.user_id)
    return {"ok": True}


@router.post("/offline")
async def offline(user: CurrentUser):
    """Clear last_seen when user closes the app."""
    def _clear(uid: str):
        from core.models import get_db_connection
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE users SET last_seen = NULL WHERE user_id = %s", (uid,))
                conn.commit()
                c.close()
        except Exception:
            pass

    await asyncio.to_thread(_clear, user.user_id)
    return {"ok": True}


@router.get("/online-users")
async def online_users(user: CurrentUser):
    """Return users active in the last 2 minutes. Admin only."""
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return await asyncio.to_thread(get_online_users)
