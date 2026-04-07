from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class InvestmentBase(BaseModel):
    item_id: int
    purchase_price: float
    quantity: int = 1
    purchase_date: Optional[datetime] = None
    purchase_fee: Optional[float] = None
    wear_value: Optional[float] = None
    notes: Optional[str] = None
    target_price: Optional[float] = None


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(BaseModel):
    purchase_price: Optional[float] = None
    quantity: Optional[int] = None
    purchase_date: Optional[datetime] = None
    purchase_fee: Optional[float] = None
    wear_value: Optional[float] = None
    notes: Optional[str] = None
    target_price: Optional[float] = None


class InvestmentSell(BaseModel):
    sold_price: float
    sold_fee: Optional[float] = None


class Investment(InvestmentBase):
    id: int
    user_id: int
    status: str = "active"
    sold_price: Optional[float] = None
    sold_at: Optional[datetime] = None
    sold_fee: Optional[float] = None
    import_source: Optional[str] = None
    steam_asset_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemDetail(BaseModel):
    id: Optional[int] = None
    market_hash_name: str
    base_name: Optional[str] = None
    item_type: str
    weapon_name: Optional[str] = None
    skin_name: Optional[str] = None
    wear: Optional[str] = None
    rarity: Optional[str] = None
    collection: Optional[str] = None
    image_url: Optional[str] = None
    is_stattrak: bool = False
    is_souvenir: bool = False

    class Config:
        from_attributes = True


class MarketPrice(BaseModel):
    price: Optional[float] = None
    currency: str = "USD"
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvestmentWithItem(BaseModel):
    id: int
    user_id: int
    item_id: Optional[int] = None
    purchase_price: float
    quantity: int
    purchase_date: Optional[datetime] = None
    purchase_fee: Optional[float] = None
    wear_value: Optional[float] = None
    notes: Optional[str] = None
    status: str
    target_price: Optional[float] = None
    sold_price: Optional[float] = None
    sold_at: Optional[datetime] = None
    sold_fee: Optional[float] = None
    import_source: Optional[str] = None
    steam_asset_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    item: ItemDetail
    prices: Dict[str, Optional[MarketPrice]] = {}
    current_price: Optional[float] = None
    current_price_currency: str = "USD"
    profit_loss: Optional[float] = None
    roi: Optional[float] = None
    current_value: Optional[float] = None
    total_invested: float
    sold_profit_loss: Optional[float] = None
    sold_roi: Optional[float] = None

    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    total_investments: int
    total_invested: float
    total_current_value: float
    total_profit_loss: float
    overall_roi: float
    priced_investments: int
    unpriced_investments: int
