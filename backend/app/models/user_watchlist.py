from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class UserWatchlist(Base):
    """
    Items a user is watching but hasn't invested in yet.

    Free tier: 20 items max (enforced at API level).
    Pro tier: unlimited.
    """
    __tablename__ = "user_watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False, index=True)

    notes = Column(String(500), nullable=True)
    added_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationships
    user = relationship("User", back_populates="watchlist")
    item = relationship("Item", back_populates="watchlist_entries")

    __table_args__ = (
        UniqueConstraint('user_id', 'item_id', name='uq_user_watchlist_item'),
    )

    def __repr__(self):
        return f"<UserWatchlist user_id={self.user_id} item_id={self.item_id}>"
