"""
Alert checker — runs after every CSFloat price update.
Checks all active price alerts against current item_prices.
When triggered: creates a Notification, marks alert inactive.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.price_alert import PriceAlert
from app.models.notification import Notification
from app.models.item_price import ItemPrice

logger = logging.getLogger(__name__)


def run_alert_check(db: Session) -> dict:
    stats = {"checked": 0, "triggered": 0, "errors": 0}

    active_alerts = db.query(PriceAlert).filter(PriceAlert.is_active == True).all()
    logger.info(f"Alert check: {len(active_alerts)} active alerts")

    for alert in active_alerts:
        try:
            # Get current price for the item+market combo
            price_row = db.query(ItemPrice).filter(
                ItemPrice.item_id == alert.item_id,
                ItemPrice.market == alert.market,
            ).first()

            if not price_row or price_row.price is None:
                stats["checked"] += 1
                continue

            current_price = price_row.price
            stats["checked"] += 1

            triggered = (
                (alert.direction == 'above' and current_price >= alert.target_price) or
                (alert.direction == 'below' and current_price <= alert.target_price)
            )

            if not triggered:
                continue

            # Mark alert as triggered
            alert.is_triggered = True
            alert.is_active = False
            alert.triggered_at = datetime.utcnow()

            # Create in-app notification
            market_label = {'csfloat': 'CSFloat', 'buff163': 'Buff163', 'steam': 'Steam'}.get(alert.market, alert.market)
            direction_label = 'above' if alert.direction == 'above' else 'below'

            notification = Notification(
                user_id=alert.user_id,
                type='price_alert',
                title=f"Price alert triggered",
                body=f"{market_label} price is {direction_label} ${alert.target_price:.2f} — now ${current_price:.2f}",
                metadata_={
                    "item_id": alert.item_id,
                    "alert_id": alert.id,
                    "price": current_price,
                    "target_price": alert.target_price,
                    "market": alert.market,
                    "direction": alert.direction,
                }
            )
            db.add(notification)
            stats["triggered"] += 1
            logger.info(f"Alert triggered: user={alert.user_id} item={alert.item_id} market={alert.market} price={current_price}")

        except Exception as e:
            logger.error(f"Alert check error for alert {alert.id}: {e}")
            stats["errors"] += 1

    db.commit()
    return stats
