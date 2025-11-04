from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PriceHistoryBase(BaseModel):
    """
    Base schema for price history
    """
    price: float = Field(..., description="Price of the item")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of price recording")
    source: str = Field(default="steam_market", description="Source of the price data")
    volume: Optional[str] = Field(None, description="Trade Volume if available")

class PriceHistoryCreate(PriceHistoryBase):
    """
    Schema for creating price history (used internally)
    """
    investment_id: int = Field(..., description="ID of the investment")


class PriceHistory(PriceHistoryBase):
    """
    Schema for returning price history data
    """
    id: int
    investment_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PriceHistoryWithItem(PriceHistory):
    """
    Schema for price history with investment details
    """
    item_name: str
    item_type: str

    class Config:
        from_attributes = True
