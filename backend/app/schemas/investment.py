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

    current_price: Optional[float] = None
    price_last_updated: Optional[datetime] = None

    @property
    def profit_loss(self) -> Optional[float]:
        """
        Calculate profit loss
        :return:
        """
        if self.current_price is not None:
            return (self.current_price - self.purchase_price) * self.quantity
        return None

    @property
    def roi_percentage(self) -> Optional[float]:
        """
        Calculate ROI percentage
        :return:
        """
        if self.current_price is not None and self.purchase_price > 0:
            return ((self.current_price - self.purchase_price) /self.purchase_price) * 100
        return None

    class Config:
        from_attributes = True
