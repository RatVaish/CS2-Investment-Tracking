from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.item import Item
from app.models.item_price import ItemPrice
from app.schemas.item import ItemCreate, ItemUpdate


def get_item(db: Session, item_id: int) -> Optional[Item]:
    """Get item by ID"""
    return db.query(Item).filter(Item.id == item_id).first()


def get_item_by_name(db: Session, market_hash_name: str) -> Optional[Item]:
    """Get item by market hash name"""
    return db.query(Item).filter(Item.market_hash_name == market_hash_name).first()


def get_items(db: Session, skip: int = 0, limit: int = 100) -> List[Item]:
    """Get all items with pagination"""
    return db.query(Item).filter(Item.is_active == True).offset(skip).limit(limit).all()


def search_items(db: Session, query: str, limit: int = 20) -> List[Item]:
    """
    Search items by name

    Args:
        db: Database session
        query: Search query
        limit: Max results

    Returns:
        List of matching items
    """
    search_term = f"%{query}%"

    return db.query(Item).filter(
        or_(
            Item.market_hash_name.ilike(search_term),
            Item.base_name.ilike(search_term),
            Item.weapon_name.ilike(search_term),
            Item.skin_name.ilike(search_term)
        ),
        Item.is_active == True
    ).limit(limit).all()


def get_items_by_type(db: Session, item_type: str, skip: int = 0, limit: int = 100) -> List[Item]:
    """Get items by type"""
    return db.query(Item).filter(
        Item.item_type == item_type,
        Item.is_active == True
    ).offset(skip).limit(limit).all()


def create_item(db: Session, item: ItemCreate) -> Item:
    """Create new item"""
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_item(db: Session, item_id: int, item_update: ItemUpdate) -> Optional[Item]:
    """Update item"""
    db_item = get_item(db, item_id)
    if not db_item:
        return None

    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


def delete_item(db: Session, item_id: int) -> bool:
    """Delete item (soft delete - set is_active to False)"""
    db_item = get_item(db, item_id)
    if not db_item:
        return False

    db_item.is_active = False
    db.commit()
    return True


def get_item_with_price(db: Session, item_id: int) -> Optional[dict]:
    """Get item with current price information"""
    item = db.query(Item).filter(Item.id == item_id).first()

    if not item:
        return None

    # Get price if exists
    price = db.query(ItemPrice).filter(ItemPrice.item_id == item_id).first()

    result = {
        **item.__dict__,
        "csfloat_price": price.csfloat_price if price else None,
        "buff_price": price.buff_price if price else None,
        "steam_price": price.steam_price if price else None
    }

    return result
