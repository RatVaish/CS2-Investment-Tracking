from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class Notification(Base):
    """
    In-app notification inbox.

    metadata JSONB carries type-specific context:
        price_alert: {"item_id": 123, "alert_id": 456, "price": 15.50, "market": "buff163"}
        item_added:  {"item_id": 789, "item_name": "AK-47 | Redline (Field-Tested)"}
        system:      {"message": "Scheduled maintenance at 2am UTC"}

    Auto-purged after 90 days.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    type = Column(String(30), nullable=False)   # 'price_alert' | 'price_drop' | 'item_added' | 'system'
    title = Column(String(255), nullable=False)
    body = Column(String(1000), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    metadata_ = Column('metadata', JSONB, nullable=True)    # Extra context per notification type

    created_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationship
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification user_id={self.user_id} type={self.type} read={self.is_read}>"
