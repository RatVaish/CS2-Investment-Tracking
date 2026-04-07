"""
Price CRUD — thin helpers for reading price data.
All writes go through price_updater.py or the dedicated clients.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.item_price import ItemPrice
from app.models.price_history import PriceHistory


def get_current_price(db: Session, item_id: int, market: str) -> Optional[ItemPrice]:
    """Get current price row for a specific item + market."""
    return db.query(ItemPrice).filter(
        ItemPrice.item_id == item_id,
        ItemPrice.market == market,
    ).first()


def get_all_prices(db: Session, item_id: int) -> dict:
    """Get all current prices for an item, keyed by market."""
    rows = db.query(ItemPrice).filter(ItemPrice.item_id == item_id).all()
    return {row.market: row for row in rows}


def get_price_history(
    db: Session,
    item_id: int,
    market: str = "steam",
    resolution: str = "daily",
    days: Optional[int] = None,
) -> List[PriceHistory]:
    """
    Get candlestick price history for an item.

    Args:
        market:     'steam' | 'csfloat' | 'buff163'
        resolution: 'hourly' | 'daily' | 'weekly'
        days:       Number of days of history (None = all)
    """
    query = db.query(PriceHistory).filter(
        PriceHistory.item_id == item_id,
        PriceHistory.market == market,
        PriceHistory.resolution == resolution,
    )

    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(PriceHistory.candle_timestamp >= cutoff)

    return query.order_by(PriceHistory.candle_timestamp.asc()).all()
