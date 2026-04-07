from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.item import Item
from app.models.item_price import ItemPrice


def get_item(db: Session, item_id: int) -> Optional[Item]:
    return db.query(Item).filter(Item.id == item_id).first()


def get_item_by_name(db: Session, market_hash_name: str) -> Optional[Item]:
    return db.query(Item).filter(Item.market_hash_name == market_hash_name).first()


def get_items(db: Session, skip: int = 0, limit: int = 100) -> List[Item]:
    return db.query(Item).filter(Item.is_active == True).offset(skip).limit(limit).all()


def search_items(db: Session, query: str, limit: int = 20) -> List[Item]:
    search_term = f"%{query}%"
    return db.query(Item).filter(
        or_(
            Item.market_hash_name.ilike(search_term),
            Item.base_name.ilike(search_term),
            Item.weapon_name.ilike(search_term),
            Item.skin_name.ilike(search_term),
        ),
        Item.is_active == True
    ).limit(limit).all()


def get_items_by_type(db: Session, item_type: str, skip: int = 0, limit: int = 100) -> List[Item]:
    return db.query(Item).filter(
        Item.item_type == item_type,
        Item.is_active == True
    ).offset(skip).limit(limit).all()


def get_item_with_price(db: Session, item_id: int) -> Optional[dict]:
    """Get item with current prices from all markets (V4)."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return None

    price_rows = db.query(ItemPrice).filter(ItemPrice.item_id == item_id).all()
    prices = {row.market: row for row in price_rows}

    csfloat = prices.get("csfloat")
    buff = prices.get("buff163")
    steam = prices.get("steam")

    from app.services.currency_utils import to_usd
    csfloat_usd = to_usd(csfloat.price, csfloat.currency or "USD") if csfloat else None
    buff_usd = to_usd(buff.price, buff.currency or "CNY") if buff else None
    steam_usd = to_usd(steam.price, steam.currency or "GBP") if steam else None

    return {
        "id": item.id,
        "market_hash_name": item.market_hash_name,
        "base_name": item.base_name,
        "item_type": item.item_type,
        "weapon_type": item.weapon_type,
        "weapon_name": item.weapon_name,
        "skin_name": item.skin_name,
        "wear": item.wear,
        "rarity": item.rarity,
        "collection": item.collection,
        "image_url": item.image_url,
        "is_stattrak": item.is_stattrak,
        "is_souvenir": item.is_souvenir,
        "is_active": item.is_active,
        "release_date": item.release_date,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "csfloat_price": csfloat_usd,
        "buff_price": buff_usd,
        "steam_price": steam_usd,
        "prices": {
            "csfloat": {"price": csfloat_usd, "currency": "USD", "updated_at": csfloat.updated_at} if csfloat else None,
            "buff163": {"price": buff_usd, "currency": "USD", "updated_at": buff.updated_at} if buff else None,
            "steam": {"price": steam_usd, "currency": "USD", "updated_at": steam.updated_at} if steam else None,
        }
    }
