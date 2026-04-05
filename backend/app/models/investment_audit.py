from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class InvestmentAudit(Base):
    """
    Full audit trail for investment changes.

    investment_id is nullable so the audit record survives
    investment deletion. Purged 90 days after the investment is deleted.

    old_values / new_values store the complete state as JSONB so
    any field can be recovered regardless of future schema changes.
    """
    __tablename__ = "investment_audit"

    id = Column(Integer, primary_key=True, index=True)

    # Nullable — survives investment deletion
    investment_id = Column(Integer, ForeignKey('investments.id', ondelete='SET NULL'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    action = Column(String(20), nullable=False)     # 'created' | 'updated' | 'sold' | 'deleted'
    old_values = Column(JSONB, nullable=True)        # State before change
    new_values = Column(JSONB, nullable=True)        # State after change

    changed_at = Column(TIMESTAMP, server_default='NOW()', nullable=False)

    # Relationships
    investment = relationship("Investment", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<InvestmentAudit investment_id={self.investment_id} action={self.action} at={self.changed_at}>"
