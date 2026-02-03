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


class ItemDetail(BaseModel):
    """Nested item details"""
    id: int
    market_hash_name: str
    item_type: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class CSFloatPriceDetail(BaseModel):
    """Nested CSFloat price details"""
    csfloat_price: Optional[float] = None

    class Config:
        from_attributes = True


class InvestmentWithItem(Investment):
    """Investment with nested item and price details"""
    item: ItemDetail
    csfloat_price: Optional[CSFloatPriceDetail] = None
    profit_loss: Optional[float] = None
    roi: Optional[float] = None

    class Config:
        from_attributes = True
