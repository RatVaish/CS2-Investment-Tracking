from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, String, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class ItemPrice(Base):
    """
    Current prices — ONE ROW PER ITEM PER MARKET (V4 normalised)

    Markets: 'csfloat' | 'buff163' | 'steam'
    Currencies: 'USD' (csfloat/steam) | 'CNY' (buff163)

    Example rows:
        item_id=1, market='csfloat', price=100.50, currency='USD'
        item_id=1, market='buff163', price=720.00, currency='CNY'
        item_id=1, market='steam',   price=110.00, currency='USD'
    """
    __tablename__ = "item_prices"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)

    # Which market this row represents
    market = Column(String(20), nullable=False)  # 'csfloat' | 'buff163' | 'steam'

    # Price data
    price = Column(Float, nullable=True)            # Main reference price
    lowest_listing = Column(Float, nullable=True)   # Lowest active listing
    highest_bid = Column(Float, nullable=True)      # Highest buy order

    # Volume metrics
    volume = Column(Integer, nullable=True)         # 24h trading volume
    listing_count = Column(Integer, nullable=True)  # Number of active listings

    # Currency — stored with the price so historical context is never lost
    currency = Column(String(3), nullable=False, default='USD')  # 'USD' | 'CNY'

    updated_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    item = relationship("Item", back_populates="prices")

    __table_args__ = (
        # One price record per item per market
        UniqueConstraint('item_id', 'market', name='uq_item_market'),
        Index('idx_item_prices_market', 'market'),
    )

    def __repr__(self):
        return f"<ItemPrice item_id={self.item_id} market={self.market} price={self.price} {self.currency}>"
