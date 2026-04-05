from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from app.db.base import Base


class UserConsent(Base):
    """
    GDPR-compliant consent audit trail.

    Every grant or revoke of consent is a new row — full history preserved.
    consent_type examples:
        'steam_inventory'     — import and store Steam inventory data
        'portfolio_history'   — store daily portfolio snapshots over time
        'marketing_emails'    — send promotional emails
    """
    __tablename__ = "user_consents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    consent_type = Column(String(50), nullable=False)   # 'steam_inventory' | 'portfolio_history' | 'marketing_emails'
    granted = Column(Boolean, nullable=False)            # True = granted, False = revoked
    granted_at = Column(TIMESTAMP, nullable=True)
    revoked_at = Column(TIMESTAMP, nullable=True)

    # Which version of privacy policy they agreed to — important for tracking policy changes
    consent_version = Column(String(20), nullable=False, default='v1.0')

    # Proof of consent — required by GDPR
    ip_address = Column(String(45), nullable=True)   # IPv6 max length
    user_agent = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="consents")

    def __repr__(self):
        return f"<UserConsent user_id={self.user_id} type={self.consent_type} granted={self.granted}>"
