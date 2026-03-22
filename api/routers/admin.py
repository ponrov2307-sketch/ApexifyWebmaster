"""Admin-only endpoints."""

from fastapi import APIRouter, HTTPException, status

from api.deps import CurrentUser
from core.models import get_online_users, update_user_last_seen

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/heartbeat")
async def heartbeat(user: CurrentUser):
    """Update last_seen for the current user. Called every 30s by the frontend."""
    update_user_last_seen(user.user_id)
    return {"ok": True}


@router.get("/online-users")
async def online_users(user: CurrentUser):
    """Return users active in the last 2 minutes. Admin only."""
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return get_online_users()
