from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class InvestmentTag(Base):
    """
    User-defined strategy tags on investments.

    Examples: 'long-hold', 'flip', 'sticker-craft', 'souvenir-target', 'risky'

    Indexed on (user_id, tag) to efficiently query
    "show all my flip trades" across thousands of investments.
    """
    __tablename__ = "investment_tags"

    id = Column(Integer, primary_key=True, index=True)
    investment_id = Column(Integer, ForeignKey('investments.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    tag = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationships
    investment = relationship("Investment", back_populates="tags")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint('investment_id', 'tag', name='uq_investment_tag'),
        Index('idx_investment_tags_user_tag', 'user_id', 'tag'),
    )

    def __repr__(self):
        return f"<InvestmentTag investment_id={self.investment_id} tag={self.tag}>"
