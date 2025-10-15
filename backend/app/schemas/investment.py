from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.investment import ItemType

class InvestmentBase(BaseModel):
    """
    Base Schema with common fields
    """
    item_name: str = Field(..., min_length=1, max_length=255)
    item_type: ItemType = ItemType.STICKER
    purchase_price: float = Field(..., gt=0)
    quantity: int = Field(default=1, ge=1)
    purchase_date: Optional[datetime] = None

class InvestmentCreate(InvestmentBase):
    """
    Schema for creating new investment (POST request)
    """
    pass

class InvestmentUpdate(InvestmentBase):
    """
    Schema for updating existing investment (POST request)
    """
    item_name: Optional[str] = Field(None, min_length=1, max_length=255)
    item_type: Optional[ItemType] = None
    purchase_price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=1)
    purchase_date: Optional[datetime] = None

class Investment(InvestmentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
