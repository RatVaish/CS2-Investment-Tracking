from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.api.deps import get_db, get_current_user
from app.schemas.user import User as UserSchema, UserUpdate, UserWithStats
from app.models.user import User
from app.crud.user import update_user
from app.models.investment import Investment

router = APIRouter()


@router.get("/me", response_model=UserSchema)
def get_current_user_profile(
        current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.

    :param current_user: Current authenticated user from JWT token
    :return: User profile
    """
    return current_user


@router.get("/me/stats", response_model=UserWithStats)
def get_current_user_with_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get current user's profile with investment statistics.

    :param current_user: Current authenticated user
    :param db: Database session
    :return: User profile with investment stats
    """
    # Get user's investments
    investments = db.query(Investment).options(
        joinedload(Investment.item),
        joinedload(Investment.csfloat_price)
    ).filter(
        Investment.user_id == current_user.id
    ).all()

    # Calculate statistics
    total_investments = len(investments)
    total_value = 0.0
    total_profit_loss = 0.0

    for inv in investments:
        if inv.csfloat_price and inv.csfloat_price.price is not None:
            current_price = inv.csfloat_price.price
            total_value += current_price * inv.quantity
            profit_loss = (current_price - inv.purchase_price) * inv.quantity
            total_profit_loss += profit_loss

    # Convert user to dict and add stats
    user_data = {
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
        "total_investments": total_investments,
        "total_value": total_value,
        "total_profit_loss": total_profit_loss
    }

    return user_data


@router.put("/me", response_model=UserSchema)
def update_current_user(
        user_update: UserUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Update current authenticated user's profile.

    :param user_update: Updated user data
    :param current_user: Current authenticated user
    :param db: Database session
    :return: Updated user profile
    :raises HTTPException: 400 if email/username already taken
    """
    # If updating email, check if it's already taken
    if user_update.email and user_update.email != current_user.email:
        from app.crud.user import get_user_by_email
        existing_user = get_user_by_email(db, email=user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )

    # If updating username, check if it's already taken
    if user_update.username and user_update.username != current_user.username:
        from app.crud.user import get_user_by_username
        existing_username = get_user_by_username(db, username=user_update.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Update user
    updated_user = update_user(db, user_id=current_user.id, user_update=user_update)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return updated_user


@router.delete("/me")
def delete_current_user(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Delete current authenticated user's account.
    This will also delete all associated investments (cascade).

    :param current_user: Current authenticated user
    :param db: Database session
    :return: Success message
    """
    from app.crud.user import delete_user

    success = delete_user(db, user_id=current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "message": "Account successfully deleted",
        "deleted_investments": "All associated investments have been deleted"
    }
