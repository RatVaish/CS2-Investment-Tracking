from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.models.investment import Investment
from app.models.item import Item
from app.models.item_price import ItemPrice
from app.schemas.investment import InvestmentCreate, InvestmentUpdate


def _get_prices(db: Session, item_id: int) -> dict:
    """Fetch all V4 price rows for an item, keyed by market."""
    rows = db.query(ItemPrice).filter(ItemPrice.item_id == item_id).all()
    return {row.market: row for row in rows}


def _to_usd(amount, currency, db):
    """Convert price to USD using exchange rates."""
    from app.services.currency_utils import to_usd
    return to_usd(amount, currency, db)


def _calc_pnl(purchase_price: float, quantity: int, current_price: Optional[float]):
    if current_price is None or purchase_price <= 0:
        return None, None
    pnl = (current_price - purchase_price) * quantity
    roi = ((current_price - purchase_price) / purchase_price) * 100
    return round(pnl, 2), round(roi, 2)


def _build_dict(inv: Investment, db: Session) -> dict:
    item = inv.item
    prices = _get_prices(db, inv.item_id) if inv.item_id else {}

    csfloat = prices.get("csfloat")
    buff = prices.get("buff163")
    steam = prices.get("steam")

    # Convert all prices to USD for consistent frontend display
    # csfloat = USD (no conversion)
    # steam = GBP (UK accounts) → USD
    # buff163 = CNY → USD
    csfloat_price_usd = _to_usd(csfloat.price, csfloat.currency or "USD", db) if csfloat else None
    buff_price_usd = _to_usd(buff.price, buff.currency or "CNY", db) if buff else None
    steam_price_usd = _to_usd(steam.price, steam.currency or "GBP", db) if steam else None

    primary_price = steam_price_usd or csfloat_price_usd
    profit_loss, roi = _calc_pnl(inv.purchase_price, inv.quantity, primary_price)

    sold_profit_loss, sold_roi = None, None
    if inv.status == "sold" and inv.sold_price:
        sold_profit_loss, sold_roi = _calc_pnl(inv.purchase_price, inv.quantity, inv.sold_price)

    return {
        "id": inv.id,
        "user_id": inv.user_id,
        "item_id": inv.item_id,
        "purchase_price": inv.purchase_price,
        "quantity": inv.quantity,
        "purchase_date": inv.purchase_date,
        "purchase_fee": inv.purchase_fee,
        "wear_value": inv.wear_value,
        "notes": inv.notes,
        "status": inv.status,
        "target_price": inv.target_price,
        "sold_price": inv.sold_price,
        "sold_at": inv.sold_at,
        "sold_fee": inv.sold_fee,
        "import_source": inv.import_source,
        "steam_asset_id": inv.steam_asset_id,
        "created_at": inv.created_at,
        "updated_at": inv.updated_at,
        "item": {
            "id": item.id if item else None,
            "market_hash_name": item.market_hash_name if item else "Unknown",
            "base_name": item.base_name if item else None,
            "item_type": item.item_type if item else "unknown",
            "weapon_name": item.weapon_name if item else None,
            "skin_name": item.skin_name if item else None,
            "wear": item.wear if item else None,
            "rarity": item.rarity if item else None,
            "collection": item.collection if item else None,
            "image_url": item.image_url if item else None,
            "is_stattrak": item.is_stattrak if item else False,
            "is_souvenir": item.is_souvenir if item else False,
        },
        "prices": {
            "csfloat": {"price": csfloat_price_usd, "currency": "USD", "updated_at": csfloat.updated_at} if csfloat else None,
            "buff163": {"price": buff_price_usd, "currency": "USD", "updated_at": buff.updated_at} if buff else None,
            "steam": {"price": steam_price_usd, "currency": "USD", "updated_at": steam.updated_at} if steam else None,
        },
        "current_price": primary_price,
        "current_price_currency": "USD",
        "profit_loss": profit_loss,
        "roi": roi,
        "current_value": round(primary_price * inv.quantity, 2) if primary_price else None,
        "total_invested": round(inv.purchase_price * inv.quantity, 2),
        "sold_profit_loss": sold_profit_loss,
        "sold_roi": sold_roi,
    }


def get_investment(db: Session, investment_id: int, user_id: int) -> Optional[Investment]:
    return db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == user_id,
    ).first()


def get_investments_with_items(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
) -> List[dict]:
    query = db.query(Investment).options(
        joinedload(Investment.item)
    ).filter(Investment.user_id == user_id)

    if status:
        query = query.filter(Investment.status == status)

    investments = query.offset(skip).limit(limit).all()
    return [_build_dict(inv, db) for inv in investments]


def get_investment_with_item(db: Session, investment_id: int, user_id: int) -> Optional[dict]:
    inv = db.query(Investment).options(
        joinedload(Investment.item)
    ).filter(
        Investment.id == investment_id,
        Investment.user_id == user_id,
    ).first()
    if not inv:
        return None
    return _build_dict(inv, db)


def create_investment(db: Session, investment: InvestmentCreate, user_id: int) -> Investment:
    db_inv = Investment(
        **investment.model_dump(),
        user_id=user_id,
        status="active",
        import_source="manual",
    )
    db.add(db_inv)
    db.commit()
    db.refresh(db_inv)
    return db_inv


def update_investment(
    db: Session, investment_id: int, user_id: int, investment_update: InvestmentUpdate
) -> Optional[Investment]:
    db_inv = get_investment(db, investment_id, user_id)
    if not db_inv:
        return None
    for key, value in investment_update.model_dump(exclude_unset=True).items():
        setattr(db_inv, key, value)
    db_inv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_inv)
    return db_inv


def sell_investment(
    db: Session, investment_id: int, user_id: int,
    sold_price: float, sold_fee: Optional[float] = None
) -> Optional[Investment]:
    db_inv = get_investment(db, investment_id, user_id)
    if not db_inv:
        return None
    db_inv.status = "sold"
    db_inv.sold_price = sold_price
    db_inv.sold_at = datetime.utcnow()
    db_inv.sold_fee = sold_fee
    db_inv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_inv)
    return db_inv


def delete_investment(db: Session, investment_id: int, user_id: int) -> bool:
    db_inv = get_investment(db, investment_id, user_id)
    if not db_inv:
        return False
    db.delete(db_inv)
    db.commit()
    return True


def get_portfolio_summary(db: Session, user_id: int) -> dict:
    investments = get_investments_with_items(db, user_id, limit=10000, status="active")

    total_investments = len(investments)
    total_invested = sum(inv["total_invested"] for inv in investments)
    priced = [inv for inv in investments if inv["current_price"] is not None]
    total_current_value = sum(inv["current_price"] * inv["quantity"] for inv in priced)
    total_profit_loss = sum(inv["profit_loss"] or 0 for inv in priced)

    invested_with_prices = sum(inv["total_invested"] for inv in priced)
    overall_roi = (total_profit_loss / invested_with_prices * 100) if invested_with_prices > 0 else 0.0

    return {
        "total_investments": total_investments,
        "total_invested": round(total_invested, 2),
        "total_current_value": round(total_current_value, 2),
        "total_profit_loss": round(total_profit_loss, 2),
        "overall_roi": round(overall_roi, 2),
        "priced_investments": len(priced),
        "unpriced_investments": total_investments - len(priced),
    }

def count_active_investments(db: Session, user_id: int) -> int:
    """Count active investments for free tier enforcement."""
    return db.query(Investment).filter(
        Investment.user_id == user_id,
        Investment.status == "active",
    ).count()
