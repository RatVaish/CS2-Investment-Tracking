from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.investment import Investment, InvestmentCreate, InvestmentUpdate, InvestmentWithItem
from app.crud import investment as crud_investment

router = APIRouter()


@router.get("/", response_model=List[InvestmentWithItem])
def get_investments(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Get all investments for the current user with item details
    """
    investments = crud_investment.get_investments_with_items(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return investments


@router.get("/{investment_id}", response_model=InvestmentWithItem)
def get_investment(
        investment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Get a specific investment by ID
    """
    investments = crud_investment.get_investments_with_items(db, user_id=current_user.id)
    investment = next((inv for inv in investments if inv["id"] == investment_id), None)

    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")

    return investment


@router.post("/", response_model=Investment, status_code=status.HTTP_201_CREATED)
def create_investment(
        investment: InvestmentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Create a new investment
    """
    return crud_investment.create_investment(
        db,
        investment=investment,
        user_id=current_user.id
    )


@router.patch("/{investment_id}", response_model=Investment)
def update_investment(
        investment_id: int,
        investment_update: InvestmentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Update an investment
    """
    updated_investment = crud_investment.update_investment(
        db,
        investment_id=investment_id,
        user_id=current_user.id,
        investment_update=investment_update
    )

    if not updated_investment:
        raise HTTPException(status_code=404, detail="Investment not found")

    return updated_investment


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(
        investment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Delete an investment
    """
    success = crud_investment.delete_investment(
        db,
        investment_id=investment_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Investment not found")

    return None
