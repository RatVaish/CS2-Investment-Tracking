from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.price_alert import PriceAlert
from app.models.item import Item

router = APIRouter()


class AlertCreate(BaseModel):
    item_id: int
    market: str        # 'steam' | 'csfloat' | 'buff163'
    target_price: float
    direction: str     # 'above' | 'below'


class AlertOut(BaseModel):
    id: int
    item_id: int
    item_name: str
    market: str
    target_price: float
    direction: str
    is_active: bool
    is_triggered: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=List[AlertOut])
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alerts = (
        db.query(PriceAlert)
        .filter(PriceAlert.user_id == current_user.id)
        .order_by(PriceAlert.created_at.desc())
        .all()
    )
    result = []
    for a in alerts:
        item = db.query(Item).filter(Item.id == a.item_id).first()
        result.append(AlertOut(
            id=a.id,
            item_id=a.item_id,
            item_name=item.market_hash_name if item else "Unknown",
            market=a.market,
            target_price=a.target_price,
            direction=a.direction,
            is_active=a.is_active,
            is_triggered=a.is_triggered,
        ))
    return result


@router.post("/", response_model=AlertOut)
def create_alert(
    data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.tier != 'pro':
        raise HTTPException(status_code=403, detail="Price alerts are a Pro feature")

    if data.direction not in ('above', 'below'):
        raise HTTPException(status_code=400, detail="direction must be 'above' or 'below'")
    if data.market not in ('steam', 'csfloat', 'buff163'):
        raise HTTPException(status_code=400, detail="market must be steam, csfloat, or buff163")

    item = db.query(Item).filter(Item.id == data.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # One active alert per item+direction per user
    existing = db.query(PriceAlert).filter(
        PriceAlert.user_id == current_user.id,
        PriceAlert.item_id == data.item_id,
        PriceAlert.direction == data.direction,
        PriceAlert.is_active == True
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"You already have an active {data.direction} alert for this item")

    alert = PriceAlert(
        user_id=current_user.id,
        item_id=data.item_id,
        market=data.market,
        target_price=data.target_price,
        direction=data.direction,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return AlertOut(
        id=alert.id,
        item_id=alert.item_id,
        item_name=item.market_hash_name,
        market=alert.market,
        target_price=alert.target_price,
        direction=alert.direction,
        is_active=alert.is_active,
        is_triggered=alert.is_triggered,
    )


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(PriceAlert).filter(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == current_user.id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()
    return {"message": "Alert deleted"}
