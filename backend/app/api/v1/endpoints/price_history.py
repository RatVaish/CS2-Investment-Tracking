from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_db
from app.schemas.price_history import PriceHistory
from app.crud.price_history import (
    get_price_history_by_investment,
    get_all_price_history,
    get_latest_price
)
from app.crud.investment import get_investment

router = APIRouter()


@router.get("/{investment_id}", response_model=List[PriceHistory])
def get_investment_price_history(
        investment_id: int,
        days: Optional[int] = Query(None, description="Filter by last N days"),
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Get price history for a specific investment

    :param investment_id: Investment ID
    :param days: Optional filter for last N days
    :param skip: Number of records to skip
    :param limit: Maximum number of records to return
    :param db: Database session
    :return: List of price history records
    """
    # Check if investment exists
    investment = get_investment(db, investment_id)
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")

    history = get_price_history_by_investment(
        db=db,
        investment_id=investment_id,
        skip=skip,
        limit=limit,
        days=days
    )

    return history


@router.get("/{investment_id}/latest", response_model=PriceHistory)
def get_investment_latest_price(
        investment_id: int,
        db: Session = Depends(get_db)
):
    """
    Get the most recent price for an investment

    :param investment_id: Investment ID
    :param db: Database session
    :return: Latest price history record
    """
    # Check if investment exists
    investment = get_investment(db, investment_id)
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")

    latest = get_latest_price(db, investment_id)
    if not latest:
        raise HTTPException(status_code=404, detail="No price history found for this investment")

    return latest


@router.get("/", response_model=List[PriceHistory])
def get_all_investments_price_history(
        days: Optional[int] = Query(None, description="Filter by last N days"),
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Get price history for all investments

    :param days: Optional filter for last N days
    :param skip: Number of records to skip
    :param limit: Maximum number of records to return
    :param db: Database session
    :return: List of all price history records
    """
    history = get_all_price_history(
        db=db,
        skip=skip,
        limit=limit,
        days=days
    )

    return history
