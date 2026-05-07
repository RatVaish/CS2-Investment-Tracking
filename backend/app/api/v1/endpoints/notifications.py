from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.notification import Notification

router = APIRouter()


class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    body: Optional[str]
    is_read: bool
    created_at: datetime
    metadata_: Optional[dict] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[NotificationOut])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return [NotificationOut(
        id=n.id,
        type=n.type,
        title=n.title,
        body=n.body,
        is_read=n.is_read,
        created_at=n.created_at,
        metadata_=n.metadata_,
    ) for n in notifications]


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    return {"count": count}


@router.post("/mark-read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}
