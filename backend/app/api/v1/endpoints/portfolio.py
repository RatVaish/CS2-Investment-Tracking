from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.api.deps import get_db
from app.models.investment import Investment
from app.models.price_history import PriceHistory

router = APIRouter()


@router.get("/value-history")
def get_portfolio_value_history(
        days: Optional[int] = Query(30, description="Number of days to look back"),
        db: Session = Depends(get_db)
):
    """
    Get portfolio value over time

    Calculates total portfolio value at each point in time based on:
    - Investment quantities
    - Historical prices

    :param days: Number of days of history to return (default 30)
    :param db: Database session
    :return: List of {timestamp, value} data points
    """

    # Get all investments with their quantities
    investments = db.query(Investment).all()

    if not investments:
        return []

    # Get price history for all investments
    investment_ids = [inv.id for inv in investments]

    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days) if days else None

    # Query price history
    query = db.query(PriceHistory).filter(PriceHistory.investment_id.in_(investment_ids))
    if cutoff_date:
        query = query.filter(PriceHistory.timestamp >= cutoff_date)

    price_history = query.order_by(PriceHistory.timestamp).all()

    # Group by timestamp to calculate portfolio value at each point
    # Key: timestamp, Value: dict of {investment_id: price}
    timeline = defaultdict(dict)

    for record in price_history:
        # Round timestamp to nearest hour for grouping
        timestamp_key = record.timestamp.replace(minute=0, second=0, microsecond=0)
        timeline[timestamp_key][record.investment_id] = record.price

    # Calculate portfolio value at each timestamp
    result = []

    # Keep track of last known price for each investment
    last_known_prices = {}

    for timestamp in sorted(timeline.keys()):
        prices_at_time = timeline[timestamp]

        # Update last known prices
        last_known_prices.update(prices_at_time)

        # Calculate total portfolio value
        total_value = 0
        for inv in investments:
            if inv.id in last_known_prices:
                total_value += last_known_prices[inv.id] * inv.quantity
            else:
                # Use purchase price if no history yet
                total_value += inv.purchase_price * inv.quantity

        result.append({
            "timestamp": timestamp.isoformat(),
            "value": round(total_value, 2)
        })

    return result


@router.get("/top-performers")
def get_top_performers(
        limit: int = Query(3, description="Number of top/bottom performers to return"),
        db: Session = Depends(get_db)
):
    """
    Get top gaining and losing investments based on price change

    :param limit: Number of top/bottom items to return (default 3)
    :param db: Database session
    :return: Dict with 'gainers' and 'losers' lists
    """
    investments = db.query(Investment).all()

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
    gainers = performers[:limit]
    losers = performers[-limit:][::-1]  # Reverse to show biggest losers first

    return {
        'gainers': gainers,
        'losers': losers
    }
