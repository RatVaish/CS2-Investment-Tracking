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


def _maybe_queue_backfill(db, item_id):
    """Fire-and-forget backfill queue — called after investment creation."""
    try:
        from app.services.backfill_queue import queue_item_for_backfill
        queue_item_for_backfill(db, item_id)
    except Exception:
        pass


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
    """Portfolio totals."""
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
    """Add a new investment. Free tier limited to 10 investments."""
    if current_user.tier == "free":
        current_count = crud_investment.count_active_investments(db, user_id=current_user.id)
        if current_count >= 10:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free tier limit reached. Upgrade to Pro for unlimited investments.",
            )
    inv = crud_investment.create_investment(
        db, investment=investment, user_id=current_user.id
    )
    _maybe_queue_backfill(db, investment.item_id)
    return inv


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


@router.get("/by-item/{item_id}")
def get_investments_by_item(
        item_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    All of the current user's positions (active + sold) for a specific item.
    Used to render trade markers on the price history chart.
    Returns lightweight trade data only — no full item detail needed.
    """
    from app.models.investment import Investment as InvestmentModel
    rows = db.query(InvestmentModel).filter(
        InvestmentModel.user_id == current_user.id,
        InvestmentModel.item_id == item_id,
    ).order_by(InvestmentModel.purchase_date.asc()).all()

    positions = []
    for inv in rows:
        positions.append({
            "id": inv.id,
            "status": inv.status,
            # Entry
            "purchase_price": inv.purchase_price,
            "quantity": inv.quantity,
            "purchase_date": inv.purchase_date.isoformat() if inv.purchase_date else None,
            "purchase_fee": inv.purchase_fee,
            # Exit (if sold)
            "sold_price": inv.sold_price,
            "sold_at": inv.sold_at.isoformat() if inv.sold_at else None,
            "sold_fee": inv.sold_fee,
            # Computed
            "total_invested": round(inv.purchase_price * inv.quantity, 2),
            "notes": inv.notes,
        })

    # Weighted average entry price across all positions
    total_qty = sum(p["quantity"] for p in positions)
    avg_entry = (
        sum(p["purchase_price"] * p["quantity"] for p in positions) / total_qty
        if total_qty > 0 else None
    )

    return {
        "item_id": item_id,
        "positions": positions,
        "total_positions": len(positions),
        "total_quantity": total_qty,
        "avg_entry_price": round(avg_entry, 4) if avg_entry else None,
        "is_dca": len(positions) > 1,
    }
