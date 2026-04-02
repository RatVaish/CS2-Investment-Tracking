from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, String, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class ItemPrice(Base):
    """
    Current prices - ONE ROW PER ITEM PER MARKET

    Old V3: One row per item with columns: csfloat_price, buff_price, steam_price
    New V4: Multiple rows per item, one for each market

    Example:
    item_id=1, market='csfloat', price=100.50
    item_id=1, market='buff163', price=95.00
    item_id=1, market='steam', price=110.00
    """
    __tablename__ = "item_prices"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)
    market = Column(String(20), nullable=False, index=True)  # 'csfloat', 'buff163', 'steam'

    # Price data
    price = Column(Float)  # Main price
    lowest_listing = Column(Float)  # Lowest available listing
    highest_bid = Column(Float)  # Highest buy order (if applicable)

    # Volume metrics
    volume = Column(Integer)  # Trading volume
    listing_count = Column(Integer)  # Number of active listings

    # Metadata
    currency = Column(String(3), default='USD')  # USD, CNY, EUR
    updated_at = Column(TIMESTAMP)

    # Relationship
    item = relationship("Item", back_populates="prices")

    # Composite unique index: one price record per item per market
    __table_args__ = (
        Index('idx_item_market', 'item_id', 'market', unique=True),
    )

    def __repr__(self):
        return f"<ItemPrice item_id={self.item_id} market={self.market} price={self.price}>"
