from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.item import Item, ItemWithPrice, ItemSearchResult
from app.crud import item as crud_item

router = APIRouter()


@router.get("/search", response_model=List[ItemSearchResult])
def search_items(
        q: str = Query(..., min_length=2, description="Search query"),
        limit: int = Query(20, le=50),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Search items by name, returns results with current prices."""
    items = crud_item.search_items(db, query=q, limit=limit)
    results = []
    for item in items:
        item_data = crud_item.get_item_with_price(db, item.id)
        if item_data:
            results.append({
                "id": item_data["id"],
                "market_hash_name": item_data["market_hash_name"],
                "base_name": item_data["base_name"],
                "item_type": item_data["item_type"],
                "wear": item_data["wear"],
                "image_url": item_data["image_url"],
                "is_stattrak": item_data["is_stattrak"],
                "csfloat_price": item_data["csfloat_price"],
                "buff_price": item_data["buff_price"],
                "steam_price": item_data["steam_price"],
            })
    return results


@router.get("/{item_id}", response_model=ItemWithPrice)
def get_item(
        item_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Get item by ID with prices from all markets."""
    item = crud_item.get_item_with_price(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/", response_model=List[Item])
def list_items(
        skip: int = 0,
        limit: int = 100,
        item_type: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """List active items with optional type filter."""
    if item_type:
        return crud_item.get_items_by_type(db, item_type=item_type, skip=skip, limit=limit)
    return crud_item.get_items(db, skip=skip, limit=limit)
