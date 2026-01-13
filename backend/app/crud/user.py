from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get user by ID

    :param db: Database session
    :param user_id: User ID
    :return: User object or None
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get user by email

    :param db: Database session
    :param email: User email
    :return: User object or None
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get user by username

    :param db: Database session
    :param username: Username
    :return: User object or None
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_steam_id(db: Session, steam_id: str) -> Optional[User]:
    """
    Get user by Steam ID

    :param db: Database session
    :param steam_id: Steam 64-bit ID
    :return: User object or None
    """
    return db.query(User).filter(User.steam_id == steam_id).first()


def create_user(db: Session, user: UserCreate) -> User:
    """
    Create a new user with email/password

    :param db: Database session
    :param user: User creation data
    :return: Created user object
    """
    hashed_password = get_password_hash(user.password)

    db_user = User(
        email=user.email,
        username=user.username,
        password_hash=hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_steam_user(db: Session, steam_id: str, username: str,
                      avatar_url: Optional[str] = None,
                      profile_url: Optional[str] = None) -> User:
    """
    Create a new user from Steam authentication

    :param db: Database session
    :param steam_id: Steam 64-bit ID
    :param username: Steam username
    :param avatar_url: Steam avatar URL
    :param profile_url: Steam profile URL
    :return: Created user object
    """
    # Generate a unique email for Steam users (they don't provide email)
    email = f"steam_{steam_id}@cs2tracker.local"

    db_user = User(
        email=email,
        username=username,
        steam_id=steam_id,
        steam_profile_url=profile_url,
        avatar_url=avatar_url,
        password_hash=None  # Steam users don't have passwords
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """
    Update user information

    :param db: Database session
    :param user_id: User ID
    :param user_update: Updated user data
    :return: Updated user object or None
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user


def update_last_login(db: Session, user_id: int) -> None:
    """
    Update user's last login timestamp

    :param db: Database session
    :param user_id: User ID
    """
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db_user.last_login = datetime.utcnow()
        db.commit()


def delete_user(db: Session, user_id: int) -> bool:
    """
    Delete a user (and all their investments via cascade)

    :param db: Database session
    :param user_id: User ID
    :return: True if deleted, False if user not found
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False

    db.delete(db_user)
    db.commit()
    return True