from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey, TIMESTAMP, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class PriceHistory(Base):
    """
    Historical daily OHLC candlestick data — ONE ROW PER ITEM PER MARKET PER DATE

    Resolution is always daily. Hourly was deprecated.
    Currency stored per-row so CNY records stay accurate if conversion logic changes.
    """
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    market = Column(String(20), nullable=False)  # 'csfloat' | 'buff163' | 'steam'
    date = Column(Date, nullable=False)

    # OHLC candlestick
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=True)

    # Volume metrics
    volume = Column(Integer, nullable=True)
    listing_count = Column(Integer, nullable=True)

    # Currency at time of recording
    currency = Column(String(3), nullable=False, default='USD')  # 'USD' | 'CNY'

    created_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationship
    item = relationship("Item", back_populates="price_history")

    __table_args__ = (
        UniqueConstraint('item_id', 'market', 'date', name='uq_item_market_date'),
        Index('idx_price_history_item_date', 'item_id', 'date'),
        Index('idx_price_history_market_date', 'item_id', 'market', 'date'),
    )

    def __repr__(self):
        return f"<PriceHistory item_id={self.item_id} market={self.market} date={self.date} close={self.close_price}>"
