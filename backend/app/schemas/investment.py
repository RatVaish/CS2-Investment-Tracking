from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InvestmentBase(BaseModel):
    item_id: int
    purchase_price: float
    quantity: int = 1
    purchase_date: Optional[datetime] = None
    notes: Optional[str] = None


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(BaseModel):
    item_id: Optional[int] = None
    purchase_price: Optional[float] = None
    quantity: Optional[int] = None
    purchase_date: Optional[datetime] = None
    notes: Optional[str] = None


class Investment(InvestmentBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvestmentWithItem(Investment):
    """Investment with item details included"""
    item_name: str
    item_type: str
    image_url: Optional[str] = None
    current_price: Optional[float] = None
    profit_loss: Optional[float] = None
    roi: Optional[float] = None

    class Config:
        from_attributes = True
