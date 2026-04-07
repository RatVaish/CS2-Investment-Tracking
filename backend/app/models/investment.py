from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='SET NULL'), nullable=True, index=True)

    # Purchase details
    purchase_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    purchase_date = Column(TIMESTAMP, nullable=True)
    purchase_fee = Column(Float, nullable=True)

    # Item specifics
    wear_value = Column(Float, nullable=True)

    # Position status
    status = Column(String(10), nullable=False, default='active')  # 'active' | 'sold'
    sold_price = Column(Float, nullable=True)
    sold_at = Column(TIMESTAMP, nullable=True)
    sold_fee = Column(Float, nullable=True)

    # User targets & notes
    target_price = Column(Float, nullable=True)
    notes = Column(String, nullable=True)

    # Import tracking
    import_source = Column(String(20), nullable=True)
    import_batch_id = Column(Integer, ForeignKey('import_batches.id', ondelete='SET NULL'), nullable=True)
    steam_asset_id = Column(String(20), nullable=True, index=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default='NOW()')
    updated_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationships — no V3 price relationship, prices fetched via item_prices table
    user = relationship("User", back_populates="investments")
    item = relationship("Item", back_populates="investments")
    stickers = relationship("InvestmentSticker", back_populates="investment", cascade="all, delete-orphan")
    tags = relationship("InvestmentTag", back_populates="investment", cascade="all, delete-orphan")
    audit_logs = relationship("InvestmentAudit", back_populates="investment")
    import_batch = relationship("ImportBatch", back_populates="investments")

    def __repr__(self):
        return f"<Investment user_id={self.user_id} item_id={self.item_id} qty={self.quantity} status={self.status}>"
