from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class User(Base):
    """
    User model for authentication and user management
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # Password hash - NULL for Steam-only accounts
    password_hash = Column(String(255), nullable=True)

    # Steam integration fields
    steam_id = Column(String(17), unique=True, nullable=True, index=True)
    steam_profile_url = Column(String(255), nullable=True)
    avatar_url = Column(String(255), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    investments = relationship("Investment", back_populates="user", cascade="all, delete-orphan")
