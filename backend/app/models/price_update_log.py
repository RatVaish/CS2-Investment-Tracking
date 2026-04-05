from sqlalchemy import Column, Integer, String, Float, TIMESTAMP
from app.db.base import Base


class PriceUpdateLog(Base):
    """
    Operational health monitoring for price update pipeline.

    Written after every scheduler price update job completes.
    When Buff stops returning data or CSFloat has an outage,
    this table shows exactly when it broke and what the error was.

    Also useful for performance tracking — if a full Buff crawl
    suddenly takes 3x longer, something changed.
    """
    __tablename__ = "price_update_log"

    id = Column(Integer, primary_key=True, index=True)
    market = Column(String(20), nullable=False)         # 'csfloat' | 'buff163' | 'steam'

    items_updated = Column(Integer, nullable=True, default=0)
    items_failed = Column(Integer, nullable=True, default=0)
    items_skipped = Column(Integer, nullable=True, default=0)

    duration_seconds = Column(Float, nullable=True)
    ran_at = Column(TIMESTAMP, server_default='NOW()')
    status = Column(String(20), nullable=False)         # 'success' | 'partial' | 'failed'
    error_msg = Column(String(1000), nullable=True)

    def __repr__(self):
        return f"<PriceUpdateLog market={self.market} status={self.status} updated={self.items_updated}>"
