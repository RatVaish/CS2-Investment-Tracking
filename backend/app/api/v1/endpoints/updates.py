from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.update import Update
from app.models.user_update_read import UserUpdateRead

router = APIRouter()


@router.get("/unread")
def get_unread_updates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all updates that the current user hasn't read yet."""
    # Get all update IDs this user has read
    read_update_ids = (
        db.query(UserUpdateRead.update_id)
        .filter(UserUpdateRead.user_id == current_user.id)
        .all()
    )
    read_ids = [r[0] for r in read_update_ids]

    # Get all updates not in that list
    unread_updates = (
        db.query(Update)
        .filter(Update.id.notin_(read_ids) if read_ids else True)
        .order_by(Update.created_at.desc())
        .all()
    )

    return [
        {
            "id": u.id,
            "title": u.title,
            "description": u.description,
            "image_url": u.image_url,
            "created_at": u.created_at,
        }
        for u in unread_updates
    ]


@router.post("/mark-read")
def mark_updates_read(
    update_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark multiple updates as read for the current user."""
    now = datetime.utcnow().isoformat()
    
    for update_id in update_ids:
        # Check if already marked as read
        existing = (
            db.query(UserUpdateRead)
            .filter(
                UserUpdateRead.user_id == current_user.id,
                UserUpdateRead.update_id == update_id
            )
            .first()
        )
        
        if not existing:
            # Create new read record
            read_record = UserUpdateRead(
                user_id=current_user.id,
                update_id=update_id,
                read_at=now
            )
            db.add(read_record)
    
    db.commit()
    return {"status": "success", "marked_count": len(update_ids)}
