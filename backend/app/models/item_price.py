from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from app.db.base import Base


class ItemPrice(Base):
    __tablename__ = "item_prices"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)

    # CSFloat prices (primary - real-time cash)
    csfloat_price = Column(Float)
    csfloat_volume = Column(Integer)
    csfloat_lowest_listing = Column(Float)
    csfloat_updated_at = Column(TIMESTAMP)

    # Buff163 prices (Chinese market cash)
    buff_price = Column(Float)
    buff_volume = Column(Integer)
    buff_updated_at = Column(TIMESTAMP)

    # Steam prices (reference only, weekly updates)
    steam_price = Column(Float)
    steam_volume = Column(Integer)
    steam_updated_at = Column(TIMESTAMP)

    # Overall tracking
    last_updated = Column(TIMESTAMP, server_default='NOW()')

    # Relationship
    item = relationship("Item", back_populates="price")

    def __repr__(self):
        return f"<ItemPrice item_id={self.item_id} csfloat={self.csfloat_price}>"
