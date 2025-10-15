from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
import enum
from datetime import datetime
from app.db.base import Base

class ItemType(str, enum.Enum):
    SKIN = "skin"
    STICKER = "sticker"
    CASE = "case"
    AGENT = "agent"
    KNIFE = "knife"
    GLOVES = "gloves"
    PATCH = "patch"
    MUSIC_KIT = "music_kit"
    GRAFFITI = "graffiti"
    OTHER = "other"

class Investment(Base):
    __tablename__ = 'investments'

    id = Column(Integer, primary_key=True, index=True)

    item_name = Column(String, index=True, nullable=False)
    item_type = Column(Enum(ItemType), default=ItemType.SKIN, nullable=False)

    purchase_price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    purchase_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
