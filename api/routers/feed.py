"""Social Feed — community trade ideas & market views."""

import asyncio

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.deps import CurrentUser
from core.models import (
    add_post_comment,
    count_user_posts_today,
    create_feed_post,
    delete_feed_post,
    delete_post_comment,
    get_feed_posts,
    get_post_comments,
    toggle_feed_like,
)

router = APIRouter(prefix="/api/feed", tags=["feed"])

PRO_ROLES = {"pro", "vip", "admin"}
DAILY_POST_LIMIT = 10
MAX_CONTENT_LENGTH = 500


class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=MAX_CONTENT_LENGTH)
    ticker: str | None = None


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=300)


@router.get("")
async def list_posts(
    user: CurrentUser,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
):
    posts = await asyncio.to_thread(get_feed_posts, offset, limit, user.user_id)
    return {"posts": posts}


@router.post("")
async def create_post(user: CurrentUser, body: PostCreate):
    if user.role.lower() not in PRO_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "PRO or ADMIN required to post")

    count = await asyncio.to_thread(count_user_posts_today, user.user_id)
    if count >= DAILY_POST_LIMIT:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, f"Limit {DAILY_POST_LIMIT} posts per day")

    ticker = body.ticker.strip().upper() if body.ticker else None
    post_id = await asyncio.to_thread(
        create_feed_post, user.user_id, user.username, user.role.lower(), body.content.strip(), ticker
    )
    if not post_id:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create post")
    return {"ok": True, "post_id": post_id}


@router.delete("/{post_id}")
async def delete_post(post_id: int, user: CurrentUser):
    is_admin = user.role.lower() == "admin"
    deleted = await asyncio.to_thread(delete_feed_post, post_id, user.user_id, is_admin)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found or not authorized")
    return {"ok": True}


@router.post("/{post_id}/like")
async def like_post(post_id: int, user: CurrentUser):
    result = await asyncio.to_thread(toggle_feed_like, post_id, user.user_id)
    return result


@router.get("/{post_id}/comments")
async def list_comments(post_id: int, user: CurrentUser):
    comments = await asyncio.to_thread(get_post_comments, post_id)
    return {"comments": comments}


@router.delete("/{post_id}/comments/{comment_id}")
async def delete_comment(post_id: int, comment_id: int, user: CurrentUser):
    is_admin = user.role.lower() == "admin"
    deleted = await asyncio.to_thread(delete_post_comment, comment_id, user.user_id, is_admin)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found or not authorized")
    return {"ok": True}


@router.post("/{post_id}/comments")
async def create_comment(post_id: int, user: CurrentUser, body: CommentCreate):
    if user.role.lower() not in PRO_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "PRO or ADMIN required to comment")

    cid = await asyncio.to_thread(
        add_post_comment, post_id, user.user_id, user.username, user.role.lower(), body.content.strip()
    )
    if not cid:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to add comment")
    return {"ok": True, "comment_id": cid}
