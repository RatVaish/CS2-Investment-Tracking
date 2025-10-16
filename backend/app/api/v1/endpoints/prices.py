from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.price_service import update_investment_price, update_all_prices
from app.crud.investment import get_investment

router = APIRouter()


@router.post("/refresh/{investment_id}")
def refresh_single_price(
        investment_id: int,
        db: Session = Depends(get_db)
):
    """
    Refresh price for a single investment

    :param investment_id: (int) ID of investment to refresh
    :param db: (Session) Database session
    :return: (dict) Update result
    """
    try:
        investment = get_investment(db, investment_id)

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
        db: Session = Depends(get_db)
):
    """
    Refresh prices for all investments

    :param db: (Session) Database session
    :return: (dict) Summary of updates
    """
    result = update_all_prices(db)

    return {
        "message": result['message'],
        "total": result['total'],
        "updated": result['updated'],
        "failed": result['failed'],
        "rate_limited": result.get('rate_limited', 0)
    }
