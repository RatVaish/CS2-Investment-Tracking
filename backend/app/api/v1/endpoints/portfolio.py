from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.crud import investment as crud_investment

router = APIRouter()


@router.get("/summary")
def get_portfolio_summary(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Get portfolio summary with totals
    """
    summary = crud_investment.get_portfolio_summary(db, user_id=current_user.id)
    return summary


@router.get("/top-performers")
def get_top_performers(
        limit: int = 5,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Get top performing investments
    """
    investments = crud_investment.get_investments_with_items(db, user_id=current_user.id, limit=1000)

    # Filter out items without current price
    valid_investments = [inv for inv in investments if inv["current_price"] is not None and inv["roi"] is not None]

    # Sort by ROI descending
    top_performers = sorted(valid_investments, key=lambda x: x["roi"], reverse=True)[:limit]
    worst_performers = sorted(valid_investments, key=lambda x: x["roi"])[:limit]

    return {
        "top_performers": top_performers,
        "worst_performers": worst_performers
    }
