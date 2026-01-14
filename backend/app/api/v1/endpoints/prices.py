from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.price import ItemPrice, PriceHistory, PriceHistoryResponse
from app.crud import price as crud_price
from app.services.price_updater import PriceUpdater

router = APIRouter()


@router.post("/refresh/{item_id}")
def refresh_item_price(
        item_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Manually refresh price for a specific item
    """
    updater = PriceUpdater(db)

    from app.crud import item as crud_item
    item = crud_item.get_item(db, item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        price_data = updater.csfloat.get_item_price(item.market_hash_name)

        if price_data:
            updater._update_item_price(item_id, 'csfloat', price_data)
            updater._record_hourly_price(item_id, 'csfloat', price_data)

            return {
                "message": "Price updated successfully",
                "item_id": item_id,
                "price": price_data.get('price')
            }
        else:
            raise HTTPException(status_code=404, detail="Price not available for this item")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update price: {str(e)}")


@router.post("/refresh-all")
def refresh_all_prices(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Manually trigger price refresh for all user's investments
    """
    from app.crud import investment as crud_investment

    investments = crud_investment.get_investments(db, user_id=current_user.id)

    if not investments:
        return {"message": "No investments to update"}

    updater = PriceUpdater(db)
    updated_count = 0

    for investment in investments:
        try:
            from app.crud import item as crud_item
            item = crud_item.get_item(db, investment.item_id)

            if item:
                price_data = updater.csfloat.get_item_price(item.market_hash_name)

                if price_data:
                    updater._update_item_price(investment.item_id, 'csfloat', price_data)
                    updater._record_hourly_price(investment.item_id, 'csfloat', price_data)
                    updated_count += 1

        except Exception as e:
            continue  # Skip failed items

    return {
        "message": f"Updated {updated_count}/{len(investments)} prices successfully",
        "updated": updated_count,
        "total": len(investments)
    }


@router.get("/{item_id}", response_model=ItemPrice)
def get_item_price(
        item_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Get current price for an item
    """
    price = crud_price.get_item_price(db, item_id)

    if not price:
        raise HTTPException(status_code=404, detail="Price not found for this item")

    return price


@router.get("/{item_id}/history", response_model=PriceHistoryResponse)
def get_price_history(
        item_id: int,
        source: str = "csfloat",
        days: int = 30,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Get price history for an item
    """
    history = crud_price.get_price_history(
        db,
        item_id=item_id,
        source=source,
        days=days
    )

    return {
        "item_id": item_id,
        "source": source,
        "data": history
    }
