from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.user import User as UserSchema, UserUpdate, UserWithStats
from app.models.user import User
from app.crud.user import update_user, get_user_by_email, get_user_by_username

router = APIRouter()


@router.get("/me", response_model=UserSchema)
def get_current_user_profile(
        current_user: User = Depends(get_current_user)
):
    """Get current user's profile."""
    return current_user


@router.get("/me/stats", response_model=UserWithStats)
def get_current_user_with_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get current user profile with portfolio statistics."""
    from app.crud.investment import get_portfolio_summary
    summary = get_portfolio_summary(db, user_id=current_user.id)

    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "steam_id": current_user.steam_id,
        "steam_profile_url": current_user.steam_profile_url,
        "avatar_url": current_user.avatar_url,
        "is_active": current_user.is_active,
        "email_verified": current_user.email_verified,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "last_login": current_user.last_login,
        "total_investments": summary["total_investments"],
        "total_value": summary["total_current_value"],
        "total_profit_loss": summary["total_profit_loss"],
    }


@router.put("/me", response_model=UserSchema)
def update_current_user(
        user_update: UserUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Update current user's profile."""
    if user_update.email and user_update.email != current_user.email:
        if get_user_by_email(db, email=user_update.email):
            raise HTTPException(status_code=400, detail="Email already in use")

    if user_update.username and user_update.username != current_user.username:
        if get_user_by_username(db, username=user_update.username):
            raise HTTPException(status_code=400, detail="Username already taken")

    updated = update_user(db, user_id=current_user.id, user_update=user_update)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.delete("/me")
def delete_current_user(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Delete current user's account and all associated data."""
    from app.crud.user import delete_user
    if not delete_user(db, user_id=current_user.id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Account successfully deleted"}
