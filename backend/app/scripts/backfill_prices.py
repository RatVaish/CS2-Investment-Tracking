"""
Backfill price history for all items

Run this script once after populating items to get 30 days of historical data.
Note: This is a simplified version - in production you'd fetch actual historical data from CSFloat API.
For now, we'll just record current prices and let the system build history going forward.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.session import SessionLocal
from app.services.price_updater import PriceUpdater
from app.services.item_manager import ItemManager
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_current_prices():
    """
    Fetch current prices for all items and record them

    This creates the initial price records. Historical data will accumulate over time
    through the hourly scheduler jobs.
    """
    logger.info("Starting price backfill for all items...")

    db = SessionLocal()
    updater = PriceUpdater(db)
    item_manager = ItemManager(db)

    try:
        # Get all active items
        items = item_manager.get_all_active_items()
        logger.info(f"Found {len(items)} items to update")

        updated_count = 0
        failed_count = 0

        for i, item in enumerate(items):
            try:
                # Get current price from CSFloat
                price_data = updater.csfloat.get_item_price(item.market_hash_name)

                if price_data:
                    # Update current price
                    updater._update_item_price(item.id, 'csfloat', price_data)

                    # Record initial hourly price point
                    updater._record_hourly_price(item.id, 'csfloat', price_data)

                    updated_count += 1
                else:
                    failed_count += 1

                # Progress update every 100 items
                if (i + 1) % 100 == 0:
                    logger.info(f"Progress: {i + 1}/{len(items)} items processed...")

                # Rate limiting - be nice to CSFloat API
                time.sleep(0.5)  # 2 requests per second max

            except Exception as e:
                logger.error(f"Failed to update price for {item.market_hash_name}: {e}")
                failed_count += 1
                continue

        logger.info(f"✅ Price backfill complete!")
        logger.info(f"   Updated: {updated_count}")
        logger.info(f"   Failed: {failed_count}")
        logger.info(f"   Total: {len(items)}")
        logger.info(f"\n📊 Historical data will accumulate automatically from hourly updates")

    except Exception as e:
        logger.error(f"Price backfill failed: {e}")
        raise
    finally:
        updater.csfloat.close()
        db.close()


if __name__ == "__main__":
    backfill_current_prices()
    