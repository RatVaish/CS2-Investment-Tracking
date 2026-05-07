from sqlalchemy import Column, Integer, String, Boolean, DateTime, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Core identity
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=True)

    # Auth
    password_hash = Column(String(255), nullable=True)

    # Google OAuth
    google_id = Column(String(255), unique=True, nullable=True, index=True)

    # Steam integration
    steam_id = Column(String(17), unique=True, nullable=True, index=True)
    steam_profile_url = Column(String(255), nullable=True)
    avatar_url = Column(String(255), nullable=True)

    # Freemium tier
    tier = Column(String(10), nullable=False, default='free')  # 'free' | 'pro'
    tier_expires_at = Column(TIMESTAMP, nullable=True)

    # Stripe billing
    stripe_customer_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True)
    subscription_status = Column(String(50), nullable=True)  # active | past_due | canceled | unpaid

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)

    # Email verification OTP
    verification_code = Column(String(6), nullable=True)
    verification_code_expires_at = Column(TIMESTAMP, nullable=True)

    # UI preferences
    preferences = Column(JSONB, nullable=True, default=dict)

    # Consent tracking
    steam_data_consent = Column(Boolean, default=False, nullable=False)
    steam_data_consent_at = Column(TIMESTAMP, nullable=True)
    terms_accepted_at = Column(TIMESTAMP, nullable=True)
    privacy_policy_accepted_at = Column(TIMESTAMP, nullable=True)

    # GDPR
    data_export_requested_at = Column(TIMESTAMP, nullable=True)
    deletion_requested_at = Column(TIMESTAMP, nullable=True)
    deletion_scheduled_at = Column(TIMESTAMP, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    investments = relationship("Investment", back_populates="user", cascade="all, delete-orphan")
    consents = relationship("UserConsent", back_populates="user", cascade="all, delete-orphan")
    portfolio_snapshots = relationship("PortfolioSnapshot", back_populates="user", cascade="all, delete-orphan")
    price_alerts = relationship("PriceAlert", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    watchlist = relationship("UserWatchlist", back_populates="user", cascade="all, delete-orphan")
    import_batches = relationship("ImportBatch", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("InvestmentAudit", back_populates="user")
    update_reads = relationship("UserUpdateRead", back_populates="user", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<User {self.username} tier={self.tier}>"
