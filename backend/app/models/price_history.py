from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey, TIMESTAMP, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    source = Column(String(20), nullable=False)  # "csfloat", "buff", "steam"
    resolution = Column(String(20), nullable=False, server_default='daily')  # ← NEW! "hourly" or "daily"
    date = Column(Date, nullable=False)

    # OHLC Candlestick data
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)

    created_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationship
    item = relationship("Item", back_populates="price_history")

    # Unique constraint - one entry per item per source per date per resolution
    __table_args__ = (
        UniqueConstraint('item_id', 'source', 'date', 'resolution', name='uq_item_source_date_resolution'),
        Index('idx_price_history_item_date', 'item_id', 'date'),
        Index('idx_price_history_resolution', 'item_id', 'resolution', 'date'),
    )

    def __repr__(self):
        return f"<PriceHistory item_id={self.item_id} source={self.source} date={self.date} resolution={self.resolution}>"
