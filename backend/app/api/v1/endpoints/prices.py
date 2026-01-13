from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.price_service import update_investment_price
from app.crud.investment import get_investment
from app.models.investment import Investment

router = APIRouter()


@router.post("/refresh/{investment_id}")
def refresh_single_price(
        investment_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Refresh price for a single investment (must be owned by authenticated user).

    :param investment_id: ID of investment to refresh
    :param current_user: Current authenticated user
    :param db: Database session
    :return: Update result
    :raises HTTPException: 404 if investment not found or not owned by user
    """
    try:
        # Get investment with ownership check
        investment = get_investment(db, investment_id, user_id=current_user.id)

        if not investment:
            raise HTTPException(status_code=404, detail="Investment not found")

        result = update_investment_price(db, investment)

        if result['success']:
            return {
                "message": result['message'],
                "investment_id": investment_id,
                "current_price": investment.current_price,
                "last_updated": investment.price_last_updated
            }
        else:
            return {
                "message": result['message'],
                "investment_id": investment_id,
                "success": False
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/refresh-all")
def refresh_all_prices(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Refresh prices for all investments belonging to the authenticated user.

    :param current_user: Current authenticated user
    :param db: Database session
    :return: Summary of updates
    """
    # Get all investments for this user
    investments = db.query(Investment).filter(
        Investment.user_id == current_user.id
    ).all()

    total = len(investments)
    updated = 0
    failed = 0
    rate_limited = 0

    for investment in investments:
        result = update_investment_price(db, investment)
        if result['success']:
            updated += 1
        else:
            if 'rate limited' in result['message'].lower():
                rate_limited += 1
            failed += 1

    return {
        "message": f"Updated {updated}/{total} prices. {rate_limited} rate limited.",
        "total": total,
        "updated": updated,
        "failed": failed,
        "rate_limited": rate_limited
    }
