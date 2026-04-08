from sqlalchemy import Column, Integer, String, Boolean, Date, TIMESTAMP, Float
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship
from app.db.base import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)

    # Identifiers
    market_hash_name = Column(String(255), unique=True, nullable=False, index=True)
    base_name = Column(String(255), nullable=False, index=True)

    # Classification
    collection = Column(String(100))
    rarity = Column(String(50))
    item_type = Column(String(50), nullable=False, index=True)
    weapon_type = Column(String(50))
    weapon_name = Column(String(50), index=True)
    skin_name = Column(String(100))
    wear = Column(String(50))

    # NEW: Doppler phase (Ruby, Sapphire, Phase 1-4, etc.)
    phase = Column(String(50), nullable=True)

    # NEW: Souvenir tournament source (e.g. "PGL Major Antwerp 2022")
    tournament = Column(String(100), nullable=True)

    # Float range — fixed per skin, critical for correct search filtering
    # NEW
    min_float = Column(Float, nullable=True)
    max_float = Column(Float, nullable=True)

    # NEW: True for perfectly fungible items (cases, capsules, basic stickers)
    is_commodity = Column(Boolean, default=False)

    # Metadata
    image_url = Column(String(500))
    is_stattrak = Column(Boolean, default=False)
    is_souvenir = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    release_date = Column(Date, nullable=True)

    # NEW: Tracks when auto-sync last touched this item
    last_synced_at = Column(TIMESTAMP, nullable=True)

    # Backfill queue — set True when an investment is added for an item with no history
    needs_backfill = Column(Boolean, nullable=False, default=False)
    backfill_attempts = Column(Integer, nullable=False, default=0)
    backfill_queued_at = Column(TIMESTAMP, nullable=True)

    # PostgreSQL full-text search vector
    search_vector = Column(TSVECTOR)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default='NOW()')
    updated_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationships
    prices = relationship("ItemPrice", back_populates="item", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="item", cascade="all, delete-orphan")
    investments = relationship("Investment", back_populates="item")
    watchlist_entries = relationship("UserWatchlist", back_populates="item", cascade="all, delete-orphan")
    price_alerts = relationship("PriceAlert", back_populates="item", cascade="all, delete-orphan")
    market_benchmarks = relationship("MarketBenchmark", back_populates="item")

    def __repr__(self):
        return f"<Item {self.market_hash_name}>"
