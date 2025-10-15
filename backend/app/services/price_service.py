from sqlalchemy.orm import Session
from app.models.investment import Investment
from app.services.steam_market import steam_market_api
from datetime import datetime
from typing import Optional

def update_investment_price(db: Session, investment: Investment) -> bool:
    """
    Fetch and update price of an investment
    :param db: (Session) Database session
    :param investment: (Investment) Investment object
    :return: (bool) True if update was successful, False otherwise
    """
    try:
        print(f"Fetching price for: {investment.item_name}")

        # Fetch price from Steam Market
        price_data = steam_market_api.get_item_price(investment.item_name)

        if price_data:
            print(f"Price data received: {price_data}")

            # Get the timestamp from price_data instead
            timestamp = price_data['timestamp']
            print(f"Timestamp to save: {timestamp}, type: {type(timestamp)}")

            # Update the investment with new price
            investment.current_price = price_data['price']
            investment.price_last_updated = timestamp  # Use the timestamp from API response

            print(f"Before commit - price_last_updated: {investment.price_last_updated}")

            db.commit()
            db.refresh(investment)

            print(f"After refresh - price_last_updated: {investment.price_last_updated}")

            return True

        return False

    except Exception as e:
        print(f"Error updating price for investment {investment.id}: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False

def update_all_prices(db: Session, skip: int = 0, limit: int = 100) -> dict:
    """
    Update prices of all investment
    :param db: (Session) Database session
    :param skip: (int) Number of rows to skip
    :param limit: (int) Number of rows to update
    :return: (dict) Updated prices dictionary
    """
    investments = db.query(Investment).offset(skip).limit(limit).all()

    total = len(investments)
    updated = 0
    failed = 0

    for investment in investments:
        if update_investment_price(db, investment):
            updated += 1
        else:
            failed += 1

    return{
        "total": total,
        "updated": updated,
        "failed": failed
    }
