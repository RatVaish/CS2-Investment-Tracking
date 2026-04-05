from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class PriceAlert(Base):
    """
    User-defined price alerts.

    Checked by the scheduler after every price update run.
    When triggered: is_triggered=True, notification created, is_active=False.

    Pro tier feature — free tier users get limited alerts.
    """
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)

    market = Column(String(20), nullable=False)         # 'csfloat' | 'buff163' | 'steam'
    target_price = Column(Float, nullable=False)
    direction = Column(String(5), nullable=False)       # 'above' | 'below'

    is_triggered = Column(Boolean, default=False, nullable=False)
    triggered_at = Column(TIMESTAMP, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationships
    user = relationship("User", back_populates="price_alerts")
    item = relationship("Item", back_populates="price_alerts")

    def __repr__(self):
        return f"<PriceAlert user_id={self.user_id} item_id={self.item_id} {self.direction} {self.target_price}>"
