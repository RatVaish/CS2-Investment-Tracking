from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from app.models.item_price import ItemPrice
from app.models.price_history import PriceHistory


def get_item_price(db: Session, item_id: int) -> Optional[ItemPrice]:
    """Get current price for an item"""
    return db.query(ItemPrice).filter(ItemPrice.item_id == item_id).first()


def get_or_create_item_price(db: Session, item_id: int) -> ItemPrice:
    """Get existing item price or create new one"""
    price = get_item_price(db, item_id)

    if not price:
        price = ItemPrice(item_id=item_id)
        db.add(price)
        db.commit()
        db.refresh(price)

    return price


def update_item_price(
        db: Session,
        item_id: int,
        source: str,
        price: float,
        volume: Optional[int] = None,
        lowest_listing: Optional[float] = None
) -> ItemPrice:
    """
    Update item price for a specific source

    Args:
        db: Database session
        item_id: Item ID
        source: "csfloat", "buff", or "steam"
        price: Current price
        volume: Trading volume
        lowest_listing: Lowest listing price (optional)

    Returns:
        Updated ItemPrice
    """
    item_price = get_or_create_item_price(db, item_id)

    if source == "csfloat":
        item_price.csfloat_price = price
        item_price.csfloat_volume = volume
        item_price.csfloat_lowest_listing = lowest_listing
        item_price.csfloat_updated_at = datetime.utcnow()
    elif source == "buff":
        item_price.buff_price = price
        item_price.buff_volume = volume
        item_price.buff_updated_at = datetime.utcnow()
    elif source == "steam":
        item_price.steam_price = price
        item_price.steam_volume = volume
        item_price.steam_updated_at = datetime.utcnow()

    item_price.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(item_price)

    return item_price


def get_price_history(
        db: Session,
        item_id: int,
        source: str = "csfloat",
        days: int = 30
) -> List[PriceHistory]:
    """
    Get price history for an item

    Args:
        db: Database session
        item_id: Item ID
        source: Price source
        days: Number of days of history

    Returns:
        List of PriceHistory records (mix of hourly + daily)
    """
    cutoff_date = date.today() - timedelta(days=days)
    thirty_days_ago = date.today() - timedelta(days=30)

    # Get hourly data for last 30 days
    recent_hourly = db.query(PriceHistory).filter(
        PriceHistory.item_id == item_id,
        PriceHistory.source == source,
        PriceHistory.date >= thirty_days_ago,
        PriceHistory.resolution == 'hourly'
    ).order_by(PriceHistory.date.asc(), PriceHistory.created_at.asc()).all()

    # Get daily data for older than 30 days
    old_daily = db.query(PriceHistory).filter(
        PriceHistory.item_id == item_id,
        PriceHistory.source == source,
        PriceHistory.date >= cutoff_date,
        PriceHistory.date < thirty_days_ago,
        PriceHistory.resolution == 'daily'
    ).order_by(PriceHistory.date.asc()).all()

    # Combine and return (old first, then recent)
    return old_daily + recent_hourly


def create_price_history(
        db: Session,
        item_id: int,
        source: str,
        resolution: str,
        price_date: date,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: Optional[int] = None
) -> PriceHistory:
    """
    Create a price history record

    Args:
        db: Database session
        item_id: Item ID
        source: Price source
        resolution: "hourly" or "daily"
        price_date: Date of the price
        open_price: Opening price
        high_price: Highest price
        low_price: Lowest price
        close_price: Closing price
        volume: Trading volume

    Returns:
        Created PriceHistory
    """
    price_history = PriceHistory(
        item_id=item_id,
        source=source,
        resolution=resolution,
        date=price_date,
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        volume=volume
    )

    db.add(price_history)
    db.commit()
    db.refresh(price_history)

    return price_history
