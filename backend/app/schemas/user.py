from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """Schema for creating a new user with email/password"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    steam_id: Optional[str] = None
    steam_profile_url: Optional[str] = None
    avatar_url: Optional[str] = None

class UserInDB(UserBase):
    """User schema as stored in database"""
    id: int
    steam_id: Optional[str] = None
    steam_profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDB):
    """User schema for API responses (excludes sensitive fields)"""
    pass


class UserWithStats(User):
    """User schema with investment statistics"""
    total_investments: int = 0
    total_value: float = 0.0
    total_profit_loss: float = 0.0