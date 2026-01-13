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
    """
    Register a new user with email and password.

    :param user_data: Registration data (email, username, password)
    :param db: Database session
    :return: Created user object
    :raises HTTPException: 400 if email or username already exists
    """
    # Check if email already exists
    existing_user = get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    existing_username = get_user_by_username(db, username=user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Create new user
    new_user = create_user(db, user=user_data)
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(
        login_data: LoginRequest,
        db: Session = Depends(get_db)
):
    """
    Login with email and password to receive JWT tokens.

    :param login_data: Login credentials (email, password)
    :param db: Database session
    :return: Access and refresh tokens
    :raises HTTPException: 401 if credentials are invalid
    """
    # Get user by email
    user = get_user_by_email(db, email=login_data.email)

    # Check if user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check if user has a password (not Steam-only account)
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Steam login. Please login with Steam."
        )

    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Update last login
    update_last_login(db, user_id=user.id)

    # Create token pair
    tokens = create_token_pair(user.id)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
        refresh_data: TokenRefreshRequest,
        db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    :param refresh_data: Refresh token
    :param db: Database session
    :return: New access and refresh tokens
    :raises HTTPException: 401 if refresh token is invalid
    """
    # Decode refresh token
    payload = decode_token(refresh_data.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Check token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # Get user ID from token
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify user still exists and is active
    from app.crud.user import get_user_by_id
    user = get_user_by_id(db, user_id=int(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new token pair
    tokens = create_token_pair(int(user_id))
    return tokens


@router.post("/logout")
def logout():
    """
    Logout endpoint (client-side token deletion).

    Note: Since we're using stateless JWT tokens, logout is handled
    client-side by deleting the tokens. This endpoint exists for
    consistency and future token blacklisting if needed.

    :return: Success message
    """
    return {
        "message": "Successfully logged out. Please delete tokens on client side."
    }
