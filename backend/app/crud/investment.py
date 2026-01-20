from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.models.investment import Investment
from app.models.item import Item
from app.models.item_price import ItemPrice
from app.schemas.investment import InvestmentCreate, InvestmentUpdate


def get_investment(db: Session, investment_id: int, user_id: int) -> Optional[Investment]:
    """Get investment by ID (with ownership check)"""
    return db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == user_id
    ).first()


def get_investments(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Investment]:
    """Get all investments for a user"""
    return db.query(Investment).filter(
        Investment.user_id == user_id
    ).offset(skip).limit(limit).all()


def get_investments_with_items(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
    """
    Get investments with NESTED item details and current prices

    Returns list of dicts with investment + nested item object
    """
    investments = db.query(Investment).options(
        joinedload(Investment.item).joinedload(Item.price)
    ).filter(
        Investment.user_id == user_id
    ).offset(skip).limit(limit).all()

    results = []
    for inv in investments:
        item = inv.item
        price = item.price if item else None

        # Get prices from different sources
        csfloat_price = price.csfloat_price if price else None
        buff_price = price.buff_price if price else None
        steam_price = price.steam_price if price else None

        # Calculate profit/loss using CSFloat as primary price
        profit_loss = None
        roi = None
        if csfloat_price:
            profit_loss = (csfloat_price - inv.purchase_price) * inv.quantity
            roi = ((csfloat_price - inv.purchase_price) / inv.purchase_price) * 100 if inv.purchase_price > 0 else 0

        # Build nested structure
        results.append({
            # Investment fields
            "id": inv.id,
            "user_id": inv.user_id,
            "item_id": inv.item_id,
            "purchase_price": inv.purchase_price,
            "quantity": inv.quantity,
            "purchase_date": inv.purchase_date,
            "notes": inv.notes,
            "created_at": inv.created_at,
            "updated_at": inv.updated_at,

            # Nested item object
            "item": {
                "id": item.id if item else None,
                "market_hash_name": item.market_hash_name if item else "Unknown",
                "item_type": item.item_type if item else "unknown",
                "image_url": item.image_url if item else None,
                "csfloat_price": csfloat_price,
                "buff_price": buff_price,
                "steam_price": steam_price
            },

            # Calculated fields
            "profit_loss": profit_loss,
            "roi": roi
        })

    return results


def create_investment(db: Session, investment: InvestmentCreate, user_id: int) -> Investment:
    """Create new investment"""
    db_investment = Investment(
        **investment.model_dump(),
        user_id=user_id
    )
    db.add(db_investment)
    db.commit()
    db.refresh(db_investment)
    return db_investment


def update_investment(
        db: Session,
        investment_id: int,
        user_id: int,
        investment_update: InvestmentUpdate
) -> Optional[Investment]:
    """Update investment (with ownership check)"""
    db_investment = get_investment(db, investment_id, user_id)
    if not db_investment:
        return None

    update_data = investment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_investment, key, value)

    db.commit()
    db.refresh(db_investment)
    return db_investment


def delete_investment(db: Session, investment_id: int, user_id: int) -> bool:
    """Delete investment (with ownership check)"""
    db_investment = get_investment(db, investment_id, user_id)
    if not db_investment:
        return False

    db.delete(db_investment)
    db.commit()
    return True


def get_portfolio_summary(db: Session, user_id: int) -> dict:
    """
    Get portfolio summary with totals

    Returns dict with total investments, total value, total P&L
    """
    investments = get_investments_with_items(db, user_id, limit=10000)  # Get all

    total_investments = len(investments)
    total_invested = sum(inv["purchase_price"] * inv["quantity"] for inv in investments)

    # Use CSFloat price as primary
    total_current_value = sum(
        (inv["item"]["csfloat_price"] or 0) * inv["quantity"]
        for inv in investments
    )
    total_profit_loss = sum(inv["profit_loss"] or 0 for inv in investments)

    overall_roi = 0
    if total_invested > 0:
        overall_roi = (total_profit_loss / total_invested) * 100

    return {
        "total_investments": total_investments,
        "total_invested": round(total_invested, 2),
        "total_current_value": round(total_current_value, 2),
        "total_profit_loss": round(total_profit_loss, 2),
        "overall_roi": round(overall_roi, 2)
    }
