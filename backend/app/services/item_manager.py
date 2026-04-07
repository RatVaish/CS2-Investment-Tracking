from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.item import Item
from app.models.item_price import ItemPrice
import logging

logger = logging.getLogger(__name__)


class ItemManager:
    """Service for managing items in the database."""

    def __init__(self, db: Session):
        self.db = db

    def search_items(self, query: str, limit: int = 20) -> List[Item]:
        search_term = f"%{query}%"
        return self.db.query(Item).filter(
            or_(
                Item.market_hash_name.ilike(search_term),
                Item.base_name.ilike(search_term),
                Item.weapon_name.ilike(search_term),
                Item.skin_name.ilike(search_term)
            ),
            Item.is_active == True
        ).limit(limit).all()

    def get_item_by_id(self, item_id: int) -> Optional[Item]:
        return self.db.query(Item).filter(Item.id == item_id).first()

    def get_item_by_name(self, market_hash_name: str) -> Optional[Item]:
        return self.db.query(Item).filter(
            Item.market_hash_name == market_hash_name
        ).first()

    def create_item(self, item_data: dict) -> Item:
        item = Item(**item_data)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        logger.info(f"Created item: {item.market_hash_name}")
        return item

    def get_or_create_item(self, market_hash_name: str, item_data: dict) -> Item:
        item = self.get_item_by_name(market_hash_name)
        if not item:
            item_data['market_hash_name'] = market_hash_name
            item = self.create_item(item_data)
        return item

    def get_all_active_items(self, limit: Optional[int] = None) -> List[Item]:
        query = self.db.query(Item).filter(Item.is_active == True)
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_items_by_type(self, item_type: str, limit: int = 100) -> List[Item]:
        return self.db.query(Item).filter(
            Item.item_type == item_type,
            Item.is_active == True
        ).limit(limit).all()

    def get_items_needing_price_update(self, market: str = "csfloat", hours: int = 1, limit: int = 1000) -> List[Item]:
        """
        Get items that need price updates for a specific market.
        V4: filters by (item_id, market) row in item_prices, not by V3 columns.
        """
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Items with no price row for this market, or stale price row
        items = self.db.query(Item).outerjoin(
            ItemPrice,
            (Item.id == ItemPrice.item_id) & (ItemPrice.market == market)
        ).filter(
            or_(
                ItemPrice.id == None,               # No price row for this market
                ItemPrice.updated_at == None,        # Never updated
                ItemPrice.updated_at < cutoff        # Stale
            ),
            Item.is_active == True
        ).limit(limit).all()

        return items
