from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class ItemPriceBase(BaseModel):
    csfloat_price: Optional[float] = None
    csfloat_volume: Optional[int] = None
    csfloat_lowest_listing: Optional[float] = None
    buff_price: Optional[float] = None
    buff_volume: Optional[int] = None
    steam_price: Optional[float] = None
    steam_volume: Optional[int] = None


class ItemPrice(ItemPriceBase):
    id: int
    item_id: int
    csfloat_updated_at: Optional[datetime] = None
    buff_updated_at: Optional[datetime] = None
    steam_updated_at: Optional[datetime] = None
    last_updated: datetime

    class Config:
        from_attributes = True


class PriceHistoryBase(BaseModel):
    source: str
    resolution: str
    date: date
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: Optional[float] = None
    volume: Optional[int] = None


class PriceHistory(PriceHistoryBase):
    id: int
    item_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    """Response for price history chart data"""
    item_id: int
    source: str
    data: list[PriceHistory]

    class Config:
        from_attributes = True
        