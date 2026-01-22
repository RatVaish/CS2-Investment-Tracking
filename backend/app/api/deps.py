from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.security import decode_token
from app.crud.user import get_user_by_id
from app.models.user import User

# Security scheme for JWT tokens
security = HTTPBearer()


def get_db() -> Generator:
    """
    Dependency that creates a new database session for each request.
    Yields the session, closing it after the request is finished.

    :return: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    :param db: Database session
    :param credentials: HTTP Bearer token from Authorization header
    :return: Current authenticated user
    :raises HTTPException: 401 if token is invalid or user not found
    """
    token = credentials.credentials

    # Decode and verify token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user ID from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Handle both email (from OAuth) and user_id (from regular login)
    try:
        user = get_user_by_id(db, user_id=int(user_id))
    except ValueError:
        # It's an email, not an ID
        from app.crud.user import get_user_by_email
        user = get_user_by_email(db, email=user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user