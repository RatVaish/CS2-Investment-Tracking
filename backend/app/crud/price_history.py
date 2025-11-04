from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.price_history import PriceHistory
from app.schemas.price_history import PriceHistoryCreate


def create_price_history(
        db: Session,
        price_history: PriceHistoryCreate
) -> PriceHistory:
    """
    Create a new price history record

    :param db: Database session
    :param price_history: Price history data
    :return: Created price history object
    """
    db_price_history = PriceHistory(**price_history.model_dump())
    db.add(db_price_history)
    db.commit()
    db.refresh(db_price_history)
    return db_price_history


def get_price_history_by_investment(
        db: Session,
        investment_id: int,
        skip: int = 0,
        limit: int = 100,
        days: Optional[int] = None
) -> List[PriceHistory]:
    """
    Get price history for a specific investment

    :param db: Database session
    :param investment_id: Investment ID
    :param skip: Number of records to skip
    :param limit: Maximum number of records to return
    :param days: Optional filter to get only last N days
    :return: List of price history records
    """
    query = db.query(PriceHistory).filter(PriceHistory.investment_id == investment_id)

    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(PriceHistory.timestamp >= cutoff_date)

    return query.order_by(PriceHistory.timestamp.desc()).offset(skip).limit(limit).all()


def get_all_price_history(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        days: Optional[int] = None
) -> List[PriceHistory]:
    """
    Get all price history records

    :param db: Database session
    :param skip: Number of records to skip
    :param limit: Maximum number of records to return
    :param days: Optional filter to get only last N days
    :return: List of all price history records
    """
    query = db.query(PriceHistory)

    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(PriceHistory.timestamp >= cutoff_date)

    return query.order_by(PriceHistory.timestamp.desc()).offset(skip).limit(limit).all()


def get_latest_price(
        db: Session,
        investment_id: int
) -> Optional[PriceHistory]:
    """
    Get the most recent price for an investment

    :param db: Database session
    :param investment_id: Investment ID
    :return: Latest price history record or None
    """
    return db.query(PriceHistory) \
        .filter(PriceHistory.investment_id == investment_id) \
        .order_by(PriceHistory.timestamp.desc()) \
        .first()


def delete_old_price_history(
        db: Session,
        days: int = 90
) -> int:
    """
    Delete price history older than specified days (for cleanup/maintenance)

    :param db: Database session
    :param days: Delete records older than this many days
    :return: Number of records deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted_count = db.query(PriceHistory) \
        .filter(PriceHistory.timestamp < cutoff_date) \
        .delete()
    db.commit()
    return deleted_count
