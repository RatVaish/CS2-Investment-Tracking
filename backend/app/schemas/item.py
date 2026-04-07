from pydantic import BaseModel
from typing import Optional, Dict
from datetime import date, datetime


class ItemBase(BaseModel):
    market_hash_name: str
    base_name: str
    collection: Optional[str] = None
    rarity: Optional[str] = None
    item_type: str
    weapon_type: Optional[str] = None
    weapon_name: Optional[str] = None
    skin_name: Optional[str] = None
    wear: Optional[str] = None
    image_url: Optional[str] = None
    is_stattrak: bool = False
    is_souvenir: bool = False
    is_active: bool = True
    release_date: Optional[date] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    is_active: Optional[bool] = None
    image_url: Optional[str] = None


class Item(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MarketPriceInfo(BaseModel):
    price: Optional[float] = None
    currency: str = "USD"
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ItemWithPrice(Item):
    """Item with current prices from all markets (V4)."""
    csfloat_price: Optional[float] = None
    buff_price: Optional[float] = None
    steam_price: Optional[float] = None
    prices: Optional[Dict[str, Optional[MarketPriceInfo]]] = {}

    class Config:
        from_attributes = True


class ItemSearchResult(BaseModel):
    """Lightweight item for search dropdown."""
    id: int
    market_hash_name: str
    base_name: Optional[str] = None
    item_type: Optional[str] = None
    wear: Optional[str] = None
    image_url: Optional[str] = None
    is_stattrak: bool = False
    csfloat_price: Optional[float] = None
    buff_price: Optional[float] = None
    steam_price: Optional[float] = None

    class Config:
        from_attributes = True
