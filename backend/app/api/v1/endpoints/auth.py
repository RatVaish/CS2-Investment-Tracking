from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    TokenRefreshRequest
)
from app.schemas.user import User as UserSchema
from app.crud.user import (
    get_user_by_email,
    get_user_by_username,
    get_user_by_id,
    create_user,
    update_last_login
)
from app.core.security import (
    verify_password,
    create_token_pair,
    decode_token
)

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register(
        user_data: RegisterRequest,
        db: Session = Depends(get_db)
):
    existing_user = get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    existing_username = get_user_by_username(db, username=user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    new_user = create_user(db, user=user_data)
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(
        login_data: LoginRequest,
        db: Session = Depends(get_db)
):
    user = get_user_by_email(db, email=login_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Steam login. Please login with Steam."
        )

    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    update_last_login(db, user_id=user.id)
    tokens = create_token_pair(user.id)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
        refresh_data: TokenRefreshRequest,
        db: Session = Depends(get_db)
):
    payload = decode_token(refresh_data.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Handle both integer user IDs and email-based subs (OAuth users)
    try:
        user = get_user_by_id(db, user_id=int(user_id))
    except ValueError:
        user = get_user_by_email(db, email=user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    tokens = create_token_pair(user.id)
    return tokens


@router.post("/logout")
def logout():
    return {
        "message": "Successfully logged out. Please delete tokens on client side."
    }
