from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.investment import Investment, InvestmentCreate, InvestmentUpdate
from app.crud.investment import (
    get_investment,
    get_investments,
    create_investment,
    update_investment,
    delete_investment
)

router = APIRouter()


@router.post("/", response_model=Investment, status_code=status.HTTP_201_CREATED)
def create_new_investment(
        investment: InvestmentCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Create a new investment for the authenticated user.

    :param investment: Investment data from request body
    :param current_user: Current authenticated user
    :param db: Database session
    :return: Created investment with ID and timestamps
    """
    return create_investment(db=db, investment=investment, user_id=current_user.id)


@router.get("/", response_model=List[Investment])
def read_investments(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all investments for the authenticated user.

    :param skip: Number of rows to skip
    :param limit: Number of rows to return
    :param current_user: Current authenticated user
    :param db: Database session
    :return: List of user's investments
    """
    investments = get_investments(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return investments


@router.get("/{investment_id}", response_model=Investment)
def read_investment(
        investment_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get a specific investment by ID (must be owned by authenticated user).

    :param investment_id: Investment ID
    :param current_user: Current authenticated user
    :param db: Database session
    :return: Investment with ID and timestamps
    :raises HTTPException: 404 if investment not found or not owned by user
    """
    db_investment = get_investment(db=db, investment_id=investment_id, user_id=current_user.id)

    if db_investment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment with id {investment_id} not found"
        )

    return db_investment


@router.patch("/{investment_id}", response_model=Investment)
def update_existing_investment(
        investment_id: int,
        investment_update: InvestmentUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Update an existing investment (must be owned by authenticated user).

    :param investment_id: Investment ID
    :param investment_update: Investment data from request body
    :param current_user: Current authenticated user
    :param db: Database session
    :return: Updated investment
    :raises HTTPException: 404 if investment not found or not owned by user
    """
    db_investment = update_investment(
        db=db,
        investment_id=investment_id,
        user_id=current_user.id,
        investment_update=investment_update
    )

    if db_investment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment with id {investment_id} not found"
        )

    return db_investment


@router.delete("/{investment_id}")
def delete_existing_investment(
        investment_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Delete an investment (must be owned by authenticated user).

    :param investment_id: Investment ID
    :param current_user: Current authenticated user
    :param db: Database session
    :return: Success message
    :raises HTTPException: 404 if investment not found or not owned by user
    """
    success = delete_investment(db=db, investment_id=investment_id, user_id=current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment with id {investment_id} not found"
        )

    return {"message": f"Investment {investment_id} successfully deleted"}
