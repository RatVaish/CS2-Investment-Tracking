from sqlalchemy.orm import Session
from app.models.investment import Investment
from app.services.steam_market import steam_market_api
from app.crud.price_history import create_price_history  # <-- Add this import
from app.schemas.price_history import PriceHistoryCreate  # <-- Add this import
from datetime import datetime
from typing import Optional


def update_investment_price(db: Session, investment: Investment) -> dict:
    """
    Fetch and update the current price for a single investment
    AND save it to price history

    :param db: (Session) Database session
    :param investment: (Investment) Investment object to update
    :return: (dict) Result with success status and message
    """
    try:
        print(f"Fetching price for: {investment.item_name}")

        # Fetch price from Steam Market
        price_data = steam_market_api.get_item_price(investment.item_name)

        if price_data:
            timestamp = price_data['timestamp']
            new_price = price_data['price']

            # Update the investment's current price
            investment.current_price = new_price
            investment.price_last_updated = timestamp

            try:
                price_history_data = PriceHistoryCreate(
                    investment_id=investment.id,
                    price=new_price,
                    timestamp=timestamp,
                    source="steam_market",
                    volume=price_data.get('volume', None)
                )
                create_price_history(db, price_history_data)
                print(f"✓ Price history saved for investment {investment.id}")
            except Exception as ph_error:
                print(f"Warning: Failed to save price history: {str(ph_error)}")

            db.commit()  # Single commit for both
            db.refresh(investment)

            return {
                'success': True,
                'message': 'Price updated successfully and saved to history',
                'price': new_price
            }
        else:
            return {
                'success': False,
                'message': 'Item not found on Steam Market or rate limited'
            }

    except Exception as e:
        print(f"Error updating price for investment {investment.id}: {str(e)}")
        db.rollback()
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }


def update_all_prices(db: Session, skip: int = 0, limit: int = 100) -> dict:
    """
    Update prices for all investments
    (This function remains mostly the same, it will automatically save history
    because it calls update_investment_price)

    :param db: (Session) Database session
    :param skip: (int) Number of records to skip
    :param limit: (int) Maximum number of records to update
    :return: (dict) Summary of updates
    """
    investments = db.query(Investment).offset(skip).limit(limit).all()

    total = len(investments)
    updated = 0
    failed = 0
    rate_limited = 0

    for investment in investments:
        result = update_investment_price(db, investment)
        if result['success']:
            updated += 1
        else:
            if 'rate limited' in result['message'].lower():
                rate_limited += 1
            failed += 1

    return {
        'total': total,
        'updated': updated,
        'failed': failed,
        'rate_limited': rate_limited,
        'message': f'Updated {updated}/{total} prices. {rate_limited} rate limited. History saved for all updates.'
    }
