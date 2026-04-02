from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey, TIMESTAMP, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class PriceHistory(Base):
    """
    Historical OHLC price data - ONE ROW PER ITEM PER MARKET PER DATE PER RESOLUTION

    Changed: 'source' → 'market' (for consistency with ItemPrice)
    """
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    market = Column(String(20), nullable=False)  # RENAMED from 'source'
    resolution = Column(String(20), nullable=False, server_default='daily')  # "hourly" or "daily"
    date = Column(Date, nullable=False)

    # OHLC Candlestick data
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)

    # Metadata
    currency = Column(String(3), default='USD')  # NEW: Track currency
    created_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationship
    item = relationship("Item", back_populates="price_history")

    # Unique constraint - UPDATED: source → market
    __table_args__ = (
        UniqueConstraint('item_id', 'market', 'date', 'resolution', name='uq_item_market_date_resolution'),
        Index('idx_price_history_item_date', 'item_id', 'date'),
        Index('idx_price_history_resolution', 'item_id', 'resolution', 'date'),
    )

    def __repr__(self):
        return f"<PriceHistory item_id={self.item_id} market={self.market} date={self.date} resolution={self.resolution}>"
