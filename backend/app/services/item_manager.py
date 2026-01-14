from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.models.item import Item
from app.models.item_price import ItemPrice
import logging

logger = logging.getLogger(__name__)


class ItemManager:
    """Service for managing items in the database"""

    def __init__(self, db: Session):
        self.db = db

    def search_items(self, query: str, limit: int = 20) -> List[Item]:
        """
        Search items using PostgreSQL full-text search

        Args:
            query: Search query (e.g., "howl mw", "ak redline ft")
            limit: Max results

        Returns:
            List of matching items
        """
        # Simple search for now (we'll add full-text search later)
        search_term = f"%{query}%"

        items = self.db.query(Item).filter(
            or_(
                Item.market_hash_name.ilike(search_term),
                Item.base_name.ilike(search_term),
                Item.weapon_name.ilike(search_term),
                Item.skin_name.ilike(search_term)
            ),
            Item.is_active == True
        ).limit(limit).all()

        return items

    def get_item_by_id(self, item_id: int) -> Optional[Item]:
        """Get item by ID"""
        return self.db.query(Item).filter(Item.id == item_id).first()

    def get_item_by_name(self, market_hash_name: str) -> Optional[Item]:
        """Get item by exact market hash name"""
        return self.db.query(Item).filter(
            Item.market_hash_name == market_hash_name
        ).first()

    def create_item(self, item_data: dict) -> Item:
        """
        Create a new item in the database

        Args:
            item_data: Dict with item information

        Returns:
            Created Item object
        """
        item = Item(**item_data)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        logger.info(f"Created item: {item.market_hash_name}")
        return item

    def get_or_create_item(self, market_hash_name: str, item_data: dict) -> Item:
        """
        Get existing item or create new one

        Args:
            market_hash_name: Item name
            item_data: Dict with item info (used if creating)

        Returns:
            Item object
        """
        item = self.get_item_by_name(market_hash_name)

        if not item:
            item_data['market_hash_name'] = market_hash_name
            item = self.create_item(item_data)

        return item

    def get_all_active_items(self, limit: Optional[int] = None) -> List[Item]:
        """Get all active items"""
        query = self.db.query(Item).filter(Item.is_active == True)

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_items_by_type(self, item_type: str, limit: int = 100) -> List[Item]:
        """Get items filtered by type"""
        return self.db.query(Item).filter(
            Item.item_type == item_type,
            Item.is_active == True
        ).limit(limit).all()

    def get_items_needing_price_update(self, hours: int = 1, limit: int = 1000) -> List[Item]:
        """
        Get items that need price updates

        Args:
            hours: Items not updated in this many hours
            limit: Max items to return

        Returns:
            List of items needing updates
        """
        # Get items where price hasn't been updated recently
        # or items with no price record at all
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        items = self.db.query(Item).outerjoin(ItemPrice).filter(
            or_(
                ItemPrice.csfloat_updated_at == None,
                ItemPrice.csfloat_updated_at < cutoff
            ),
            Item.is_active == True
        ).limit(limit).all()

        return items
