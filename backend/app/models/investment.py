from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='SET NULL'), nullable=False, index=True)

    # User investment data
    purchase_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    purchase_date = Column(TIMESTAMP)
    notes = Column(String)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default='NOW()')
    updated_at = Column(TIMESTAMP, server_default='NOW()', onupdate='NOW()')

    # Relationships
    user = relationship("User", back_populates="investments")
    item = relationship("Item", back_populates="investments")

    def __repr__(self):
        return f"<Investment user_id={self.user_id} item_id={self.item_id} qty={self.quantity}>"
