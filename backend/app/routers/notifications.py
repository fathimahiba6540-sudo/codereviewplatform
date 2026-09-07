from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.notification import Notification
from backend.app.models.schemas import APIResponse
from backend.app.routers.deps import get_current_active_user

router = APIRouter(tags=["Notifications"])


@router.get("/notifications", status_code=status.HTTP_200_OK)
def get_user_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all notifications for the authenticated user."""
    notifications = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).all()

    return APIResponse(
        success=True,
        message=f"Retrieved {len(notifications)} notification(s)",
        data=[
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "notification_type": n.notification_type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]
    )


@router.put("/notifications/{notification_id}/read", status_code=status.HTTP_200_OK)
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark a notification as read."""
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if n:
        n.is_read = True
        db.commit()

    return APIResponse(
        success=True,
        message="Notification marked as read",
        data={"id": notification_id, "is_read": True}
    )
