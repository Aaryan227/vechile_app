from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.schemas.notification import (
    NotificationInboxResponse,
    NotificationItemResponse,
    UnreadCountResponse
)
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["In-App Notifications (Bell Icon)"])


@router.get("", response_model=NotificationInboxResponse)
def get_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Limit for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve notification inbox history for the currently logged-in user with unread badge count."""
    notifications, unread_count, total_count = notification_service.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        skip=skip,
        limit=limit
    )
    return NotificationInboxResponse(
        unread_count=unread_count,
        total_count=total_count,
        notifications=notifications
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the unread notification badge count for the bell icon."""
    count = notification_service.get_unread_notification_count(db=db, user_id=current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationItemResponse)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an individual notification as read when tapped by the user."""
    return notification_service.mark_notification_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )


@router.post("/read-all")
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all unread notifications as read (e.g. 'Mark all as read' button in app)."""
    marked_count = notification_service.mark_all_notifications_as_read(
        db=db,
        user_id=current_user.id
    )
    return {
        "message": "All notifications marked as read.",
        "marked_read_count": marked_count
    }


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dismiss or delete a notification from the inbox."""
    notification_service.delete_user_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    return {"message": "Notification deleted successfully."}
