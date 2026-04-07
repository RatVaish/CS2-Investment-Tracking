from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.investment import (
    Investment, InvestmentCreate, InvestmentUpdate,
    InvestmentWithItem, InvestmentSell, PortfolioSummary
)
from app.crud import investment as crud_investment

router = APIRouter()


@router.get("/", response_model=List[InvestmentWithItem])
def get_investments(
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = Query(None, description="active | sold"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Get all investments with item details and prices."""
    return crud_investment.get_investments_with_items(
        db, user_id=current_user.id, skip=skip, limit=limit, status=status
    )


@router.get("/summary", response_model=PortfolioSummary)
def get_portfolio_summary(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Portfolio totals — invested, current value, P&L, ROI."""
    return crud_investment.get_portfolio_summary(db, user_id=current_user.id)


@router.get("/{investment_id}", response_model=InvestmentWithItem)
def get_investment(
        investment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Get a single investment with full details."""
    inv = crud_investment.get_investment_with_item(
        db, investment_id=investment_id, user_id=current_user.id
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
    return inv


@router.post("/", response_model=Investment, status_code=status.HTTP_201_CREATED)
def create_investment(
        investment: InvestmentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Add a new investment."""
    return crud_investment.create_investment(
        db, investment=investment, user_id=current_user.id
    )


@router.patch("/{investment_id}", response_model=Investment)
def update_investment(
        investment_id: int,
        investment_update: InvestmentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Update an investment."""
    updated = crud_investment.update_investment(
        db, investment_id=investment_id,
        user_id=current_user.id, investment_update=investment_update
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Investment not found")
    return updated


@router.post("/{investment_id}/sell", response_model=Investment)
def sell_investment(
        investment_id: int,
        sell_data: InvestmentSell,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Mark an investment as sold."""
    inv = crud_investment.get_investment(db, investment_id, current_user.id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
    if inv.status == "sold":
        raise HTTPException(status_code=400, detail="Already sold")
    return crud_investment.sell_investment(
        db, investment_id=investment_id, user_id=current_user.id,
        sold_price=sell_data.sold_price, sold_fee=sell_data.sold_fee
    )


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(
        investment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Delete an investment."""
    if not crud_investment.delete_investment(db, investment_id, current_user.id):
        raise HTTPException(status_code=404, detail="Investment not found")
