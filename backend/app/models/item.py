from sqlalchemy import Column, Integer, String, Boolean, Date, TIMESTAMP
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

    # Metadata
    image_url = Column(String(500))
    is_stattrak = Column(Boolean, default=False)
    is_souvenir = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    release_date = Column(Date)

    # Search optimization (PostgreSQL full-text search)
    search_vector = Column(TSVECTOR)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default='NOW()')
    updated_at = Column(TIMESTAMP, server_default='NOW()', onupdate='NOW()')

    # Relationships
    price = relationship("ItemPrice", back_populates="item", uselist=False, cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="item", cascade="all, delete-orphan")
    investments = relationship("Investment", back_populates="item")

    def __repr__(self):
        return f"<Item {self.market_hash_name}>"
