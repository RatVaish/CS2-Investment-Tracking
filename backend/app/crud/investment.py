from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.investment import Investment
from app.schemas.investment import InvestmentCreate, InvestmentUpdate

def get_investment(db: Session, investment_id: int) -> Optional[Investment]:
    """
    Get a single investment by ID
    :param db: (str) Database session
    :param investment_id: (int) Investment ID
    :return: (Investment|None) Investment object if found, None otherwise
    """
    return db.query(Investment).filter(Investment.id == investment_id).first()

def get_investments(
        db: Session,
        skip: int=0,
        limit: int=100
) -> List[Investment]:
    """
    Get all investments
    :param db: (Session) Database session
    :param skip: (int) Number of records to skip
    :param limit: (int) Number of records to return
    :return: (List[Investment]) List of all investment objects
    """
    return db.query(Investment).offset(skip).limit(limit).all()

def create_investment(
        db: Session,
        investment: InvestmentCreate
) -> Investment:
    """
    Create an investment
    :param db: (Session) Database session
    :param investment: (InvestmentCreate) Investment data from request
    :return: (Investment) Investment object with IDs and timestamps
    """
    db_investment = Investment(**investment.model_dump())
    db.add(db_investment)
    db.commit()
    db.refresh(db_investment)
    return db_investment

def update_investment(
        db: Session,
        investment_id: int,
        investment_update: InvestmentUpdate
) -> Optional[Investment]:
    """
    Update an investment
    :param db: (Session) Database session
    :param investment_id: (int) Investment ID
    :param investment_update: (InvestmentUpdate) Investment data from request
    :return: (Investment|None) Investment object if found, None otherwise
    """
    db_investment = get_investment(db, investment_id)
    if db_investment is None:
        return None

    update_data = investment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_investment, field, value)

    db.commit()
    db.refresh(db_investment)
    return db_investment

def delete_investment(db: Session, investment_id: int) -> bool:
    """
    Delete an investment by ID
    :param db: (Session) Database session
    :param investment_id: (int) Investment ID
    :return: (bool) True if deleted, False otherwise
    """
    db_investment = get_investment(db, investment_id)
    if db_investment is None:
        return False

    db.delete(db_investment)
    db.commit()
    return True
