from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.investment import Investment
from app.schemas.investment import InvestmentCreate, InvestmentUpdate


def get_investment(db: Session, investment_id: int, user_id: int) -> Optional[Investment]:
    """
    Get a single investment by ID for a specific user.

    :param db: Database session
    :param investment_id: Investment ID
    :param user_id: User ID (for ownership verification)
    :return: Investment object if found and owned by user, None otherwise
    """
    return db.query(Investment).filter(
        Investment.id == investment_id,
        Investment.user_id == user_id
    ).first()


def get_investments(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
) -> List[Investment]:
    """
    Get all investments for a specific user.

    :param db: Database session
    :param user_id: User ID to filter investments
    :param skip: Number of records to skip
    :param limit: Number of records to return
    :return: List of investment objects for the user
    """
    return db.query(Investment).filter(
        Investment.user_id == user_id
    ).offset(skip).limit(limit).all()


def create_investment(
        db: Session,
        investment: InvestmentCreate,
        user_id: int
) -> Investment:
    """
    Create an investment for a specific user.

    :param db: Database session
    :param investment: Investment data from request
    :param user_id: User ID to associate with investment
    :return: Investment object with IDs and timestamps
    """
    # Create investment with user_id
    db_investment = Investment(
        **investment.model_dump(),
        user_id=user_id
    )

    db.add(db_investment)
    db.commit()
    db.refresh(db_investment)
    return db_investment


def update_investment(
        db: Session,
        investment_id: int,
        user_id: int,
        investment_update: InvestmentUpdate
) -> Optional[Investment]:
    """
    Update an investment (with ownership verification).

    :param db: Database session
    :param investment_id: Investment ID
    :param user_id: User ID (for ownership verification)
    :param investment_update: Investment data from request
    :return: Investment object if found and updated, None otherwise
    """
    # Get investment with ownership check
    db_investment = get_investment(db, investment_id, user_id)
    if db_investment is None:
        return None

    # Update fields
    update_data = investment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_investment, field, value)

    db.commit()
    db.refresh(db_investment)
    return db_investment


def delete_investment(db: Session, investment_id: int, user_id: int) -> bool:
    """
    Delete an investment (with ownership verification).

    :param db: Database session
    :param investment_id: Investment ID
    :param user_id: User ID (for ownership verification)
    :return: True if deleted, False otherwise
    """
    # Get investment with ownership check
    db_investment = get_investment(db, investment_id, user_id)
    if db_investment is None:
        return False

    db.delete(db_investment)
    db.commit()
    return True


def get_investment_count(db: Session, user_id: int) -> int:
    """
    Get total count of investments for a user.

    :param db: Database session
    :param user_id: User ID
    :return: Count of investments
    """
    return db.query(Investment).filter(Investment.user_id == user_id).count()
