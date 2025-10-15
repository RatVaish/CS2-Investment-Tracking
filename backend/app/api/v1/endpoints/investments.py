from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
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
    db: Session = Depends(get_db)
):
    """
    Create a new investment
    :param investment: (InvestmentCreate) Investment data from request body
    :param db: (Session) db session
    :return: (Investment) Created investment with ID and timestamps
    """
    return create_investment(db=db, investment=investment)

@router.get("/", response_model=List[Investment])
def read_investments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all investments
    :param skip: (int) Number of rows to skip
    :param limit: (int) Number of rows to return
    :param db: (session) db session
    :return: (List[Investment]) List of all investments
    """
    investments = get_investments(db=db, skip=skip, limit=limit)
    return investments

@router.get("/{investment_id}", response_model=Investment)
def read_investment(
    investment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get an investment by ID
    :param investment_id: (int) Investment ID
    :param db: (session) db session
    :return: (Investment) Investment with ID and timestamps
    :raises HTTPException: 404 if investment not found
    """
    db_investment = get_investment(db=db, investment_id=investment_id)
    if db_investment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment with id {investment_id} not found"
        )
    return db_investment

@router.patch("/{investment_id}", response_model=Investment)
def  update_existing_investment(
    investment_id: int,
    investment_update: InvestmentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing investment
    :param investment_id: (int) Investment ID
    :param investment: (InvestmentUpdate) Investment data from request body
    :param db: (session) db session
    :return: (Investment) Updated investment with ID and timestamps
    :raises HTTPException: 404 if investment not found
    """
    db_investment = update_investment(
        db=db,
        investment_id=investment_id,
        investment_update=investment_update
    )
    if db_investment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment with id {investment_id} not found"
        )
    return db_investment


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_investment(
        investment_id: int,
        db: Session = Depends(get_db)
):
    """
    Delete an investment by ID

    :param investment_id: (int) The ID of the investment to delete
    :param db: (Session) Database session (injected)
    :return: (None) No content on success
    :raises HTTPException: 404 if investment not found
    """
    deleted = delete_investment(db=db, investment_id=investment_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment with id {investment_id} not found"
        )
    return None
