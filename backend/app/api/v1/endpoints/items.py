from typing import List
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
    """
    Search for items by name
    """
    items = crud_item.search_items(db, query=q, limit=limit)

    # Include prices in search results
    results = []
    for item in items:
        item_with_price = crud_item.get_item_with_price(db, item.id)
        if item_with_price:
            results.append({
                "id": item.id,
                "market_hash_name": item.market_hash_name,
                "image_url": item.image_url,
                "csfloat_price": item_with_price.get("csfloat_price")
            })

    return results


@router.get("/{item_id}", response_model=ItemWithPrice)
def get_item(
        item_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Get item by ID with price information
    """
    item = crud_item.get_item_with_price(db, item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item


@router.get("/", response_model=List[Item])
def list_items(
        skip: int = 0,
        limit: int = 100,
        item_type: str = Query(None, description="Filter by item type"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    List all items with optional filtering
    """
    if item_type:
        items = crud_item.get_items_by_type(db, item_type=item_type, skip=skip, limit=limit)
    else:
        items = crud_item.get_items(db, skip=skip, limit=limit)

    return items
