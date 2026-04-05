from sqlalchemy import Column, Integer, Float, String, ForeignKey, TIMESTAMP, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class PriceHistory(Base):
    """
    OHLV candlestick price history — one row per item per market per candle period.

    Resolutions:
        'hourly'  — last 30 days, candle_timestamp = start of that hour
        'daily'   — 30 days to 1 year, candle_timestamp = midnight of that day
        'weekly'  — older than 1 year, candle_timestamp = Monday midnight of that week

    candle_timestamp examples:
        hourly:  2026-04-05 14:00:00
        daily:   2026-04-05 00:00:00
        weekly:  2026-03-30 00:00:00  (Monday)

    Data source: Steam price history endpoint (real completed sales)
    Currency: USD for Steam/CSFloat, CNY for Buff
    """
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    market = Column(String(20), nullable=False)       # 'steam' | 'csfloat' | 'buff163'
    resolution = Column(String(10), nullable=False)   # 'hourly' | 'daily' | 'weekly'
    candle_timestamp = Column(TIMESTAMP, nullable=False)  # start of candle period

    # OHLV
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=True)
    volume = Column(Integer, nullable=True)

    # Currency stored per-row
    currency = Column(String(3), nullable=False, default='USD')

    created_at = Column(TIMESTAMP, server_default='NOW()')
    updated_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationship
    item = relationship("Item", back_populates="price_history")

    __table_args__ = (
        UniqueConstraint(
            'item_id', 'market', 'candle_timestamp', 'resolution',
            name='uq_item_market_timestamp_resolution'
        ),
        Index('idx_ph_item_market_resolution_ts', 'item_id', 'market', 'resolution', 'candle_timestamp'),
        Index('idx_ph_item_ts', 'item_id', 'candle_timestamp'),
    )

    def __repr__(self):
        return (
            f"<PriceHistory item_id={self.item_id} market={self.market} "
            f"resolution={self.resolution} ts={self.candle_timestamp} close={self.close_price}>"
        )
