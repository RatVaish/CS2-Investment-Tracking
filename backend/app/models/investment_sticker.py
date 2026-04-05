from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class InvestmentSticker(Base):
    """
    Stickers applied to an investment item.

    CS2 skins can have up to 4 sticker slots (0-3), plus a keychain slot (4).
    Sticker wear (scrape level) significantly affects value — a pristine Kato 2014
    sticker is worth far more than a 95% scraped one.

    This table is critical for accurate P&L on stickered investments.
    """
    __tablename__ = "investment_stickers"

    id = Column(Integer, primary_key=True, index=True)
    investment_id = Column(Integer, ForeignKey('investments.id', ondelete='CASCADE'), nullable=False, index=True)

    slot = Column(Integer, nullable=False)              # 0-3 = sticker slots, 4 = keychain
    sticker_name = Column(String(255), nullable=False)  # Full market name of the sticker
    sticker_wear = Column(Float, nullable=True)         # 0.0 (pristine) to 1.0 (fully scraped)
    applied_at = Column(TIMESTAMP, nullable=True)       # When sticker was applied (if known)
    purchase_value = Column(Float, nullable=True)       # Sticker's value at time of application

    # Relationship
    investment = relationship("Investment", back_populates="stickers")

    __table_args__ = (
        # Only one sticker per slot per investment
        UniqueConstraint('investment_id', 'slot', name='uq_investment_sticker_slot'),
    )

    def __repr__(self):
        return f"<InvestmentSticker investment_id={self.investment_id} slot={self.slot} sticker={self.sticker_name}>"
