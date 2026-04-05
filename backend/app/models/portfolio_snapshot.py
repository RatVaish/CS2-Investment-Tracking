from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class PortfolioSnapshot(Base):
    """
    Daily snapshot of a user's total portfolio value.

    One row per user per day, written by the daily scheduler.
    Powers the "portfolio value over time" chart — without this,
    you can only show individual item history, not total portfolio growth.

    csfloat_value and buff_value allow market-specific breakdowns
    since Buff and CSFloat prices differ significantly.
    """
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Aggregate portfolio values
    total_invested = Column(Float, nullable=False)
    total_current_value = Column(Float, nullable=False)
    total_profit_loss = Column(Float, nullable=False)
    overall_roi = Column(Float, nullable=False)

    # Per-market breakdown
    csfloat_value = Column(Float, nullable=True)    # Total value using CSFloat prices
    buff_value = Column(Float, nullable=True)        # Total value using Buff prices (USD equivalent)

    # Count of open positions at snapshot time
    open_positions = Column(Integer, nullable=True)

    snapshot_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationship
    user = relationship("User", back_populates="portfolio_snapshots")

    __table_args__ = (
        UniqueConstraint('user_id', 'snapshot_date', name='uq_user_snapshot_date'),
    )

    def __repr__(self):
        return f"<PortfolioSnapshot user_id={self.user_id} date={self.snapshot_date} value={self.total_current_value}>"
