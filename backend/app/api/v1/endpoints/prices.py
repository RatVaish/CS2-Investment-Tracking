from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import traceback

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
    Refresh price from Steam Market for a single investment.
    :param investment_id: (int) ID of investment to refresh.
    :param db: (Session) Database session.
    :return: (dict) Update result
    """
    try:
        investment = get_investment(db, investment_id)

        if not investment:
            raise HTTPException(status_code=404, detail="Investment not found")

        success = update_investment_price(db, investment)

        if success:
            return{
                "message": "Price successfully updated",
                "investment_id": investment.id,
                "current_price": investment.current_price,
                "last_updated": investment.price_last_updated
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to fetch price from Steam Market"
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in refresh_single_price: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/refresh-all")
def refresh_all_prices(
    db: Session = Depends(get_db)
):
    """
    Refresh all price from Steam Market for all investments.

    :param db: (session) Database session.
    :return: (dict) Summary of updates
    """
    results = update_all_prices(db)

    return{
        "message": "Price refresh completed",
        **results
    }
