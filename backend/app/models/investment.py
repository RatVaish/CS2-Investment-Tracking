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
    purchase_fee = Column(Float, nullable=True)         # NEW: fees paid on purchase (Steam tax, etc.)

    # Item specifics — NEW
    wear_value = Column(Float, nullable=True)           # Actual float value (0.0 - 1.0)

    # Position status — NEW
    status = Column(String(10), nullable=False, default='active')  # 'active' | 'sold'
    sold_price = Column(Float, nullable=True)           # Exit price per unit
    sold_at = Column(TIMESTAMP, nullable=True)
    sold_fee = Column(Float, nullable=True)             # Fees paid on sale

    # User targets & notes
    target_price = Column(Float, nullable=True)         # NEW: price target for this investment
    notes = Column(String, nullable=True)

    # Import tracking — NEW
    import_source = Column(String(20), nullable=True)   # 'manual' | 'steam' | 'csv' | 'excel' | 'skinport'
    import_batch_id = Column(Integer, ForeignKey('import_batches.id', ondelete='SET NULL'), nullable=True)
    steam_asset_id = Column(String(20), nullable=True, index=True)  # Unique Steam item instance ID

    # Timestamps
    created_at = Column(TIMESTAMP, server_default='NOW()')
    updated_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationships
    user = relationship("User", back_populates="investments")
    item = relationship("Item", back_populates="investments")
    stickers = relationship("InvestmentSticker", back_populates="investment", cascade="all, delete-orphan")
    tags = relationship("InvestmentTag", back_populates="investment", cascade="all, delete-orphan")
    audit_logs = relationship("InvestmentAudit", back_populates="investment")
    import_batch = relationship("ImportBatch", back_populates="investments")

    def __repr__(self):
        return f"<Investment user_id={self.user_id} item_id={self.item_id} qty={self.quantity} status={self.status}>"
