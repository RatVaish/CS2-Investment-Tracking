from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class PriceHistory(Base):
    """
    Model for storing historical price data for investments
    """
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True, index=True)
    investment_id = Column(Integer, ForeignKey("investments.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = Column(String, default="steam_market", nullable=False)
    volume = Column(String, nullable=True)  # Optional: track trading volume if available
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to Investment
    #investment = relationship(
    #    "app.models.investment.Investment",
    #    back_populates="price_history"
    #)

    def __repr__(self):
        return f"<PriceHistory(id={self.id}, investment_id={self.investment_id}, price={self.price}, timestamp={self.timestamp})>"