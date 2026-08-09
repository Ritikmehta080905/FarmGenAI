"""
backend/routes/notification_routes.py

Notification management endpoints.
In-memory notification store backed by Database.history.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from backend.services.security import get_current_user
from database.db import Database

router = APIRouter(tags=["Notifications"])

# In-memory notification store keyed by user_id
_notifications: dict = {}


async def _add_notification(user_id: str, title: str, message: str, notif_type: str = "INFO"):
    notif = {
        "id": str(uuid.uuid4())[:8],
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": notif_type,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _notifications.setdefault(user_id, []).append(notif)
    return notif


@router.get("/")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    """Return all notifications for the authenticated user."""
    uid = current_user["sub"]
    notifs = _notifications.get(uid, [])
    # Most recent first
    return {"success": True, "data": list(reversed(notifs)), "unread_count": sum(1 for n in notifs if not n["read"])}


@router.post("/mark-read/{notification_id}")
async def mark_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a specific notification as read."""
    uid = current_user["sub"]
    for n in _notifications.get(uid, []):
        if n["id"] == notification_id:
            n["read"] = True
            return {"success": True, "message": "Notification marked as read."}
    return {"success": False, "message": "Notification not found."}


@router.post("/mark-all-read")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read for the authenticated user."""
    uid = current_user["sub"]
    for n in _notifications.get(uid, []):
        n["read"] = True
    return {"success": True, "message": "All notifications marked as read."}


@router.delete("/clear")
async def clear_notifications(current_user: dict = Depends(get_current_user)):
    """Clear all notifications for the authenticated user."""
    uid = current_user["sub"]
    _notifications[uid] = []
    return {"success": True, "message": "All notifications cleared."}


@router.post("/send")
async def send_notification(
    user_id: str,
    title: str,
    message: str,
    notif_type: str = "INFO",
    current_user: dict = Depends(get_current_user),
):
    """Admin endpoint to send a notification to any user."""
    notif = _add_notification(user_id, title, message, notif_type)
    return {"success": True, "data": notif}


# Export helper for internal use
async def create_notification(user_id: str, title: str, message: str, notif_type: str = "INFO"):
    return _add_notification(user_id, title, message, notif_type)
