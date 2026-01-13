from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.investment import Investment

router = APIRouter()


@router.get("/summary")
def get_portfolio_summary(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get portfolio summary statistics for the authenticated user.

    :param current_user: Current authenticated user
    :param db: Database session
    :return: Portfolio summary with totals and statistics
    """
    # Get all investments for this user
    investments = db.query(Investment).filter(
        Investment.user_id == current_user.id
    ).all()

    if not investments:
        return {
            "total_investments": 0,
            "total_invested": 0.0,
            "current_value": 0.0,
            "total_profit_loss": 0.0,
            "roi_percentage": 0.0
        }

    total_invested = sum(inv.purchase_price * inv.quantity for inv in investments)
    current_value = sum(
        (inv.current_price or inv.purchase_price) * inv.quantity
        for inv in investments
    )
    total_profit_loss = current_value - total_invested
    roi_percentage = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0.0

    return {
        "total_investments": len(investments),
        "total_invested": round(total_invested, 2),
        "current_value": round(current_value, 2),
        "total_profit_loss": round(total_profit_loss, 2),
        "roi_percentage": round(roi_percentage, 2)
    }


@router.get("/top-performers")
def get_top_performers(
        limit: int = Query(3, description="Number of top/bottom performers to return"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get top gaining and losing investments for the authenticated user based on price change.

    :param limit: Number of top/bottom items to return (default 3)
    :param current_user: Current authenticated user
    :param db: Database session
    :return: Dict with 'gainers' and 'losers' lists
    """
    investments = db.query(Investment).filter(
        Investment.user_id == current_user.id
    ).all()

    performers = []

    for inv in investments:
        if inv.current_price and inv.purchase_price:
            price_change = inv.current_price - inv.purchase_price
            price_change_pct = ((price_change / inv.purchase_price) * 100) if inv.purchase_price > 0 else 0
            total_profit_loss = price_change * inv.quantity

            performers.append({
                'id': inv.id,
                'item_name': inv.item_name,
                'item_type': inv.item_type.value,
                'purchase_price': inv.purchase_price,
                'current_price': inv.current_price,
                'quantity': inv.quantity,
                'price_change': round(price_change, 2),
                'price_change_pct': round(price_change_pct, 2),
                'total_profit_loss': round(total_profit_loss, 2)
            })

    # Sort by percentage change
    performers.sort(key=lambda x: x['price_change_pct'], reverse=True)

    # Get top gainers and losers
    gainers = performers[:limit] if performers else []
    losers = performers[-limit:][::-1] if len(performers) >= limit else []

    return {
        'gainers': gainers,
        'losers': losers
    }