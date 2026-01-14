from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from typing import List, Optional
from app.models.item import Item
from app.models.item_price import ItemPrice
from app.models.price_history import PriceHistory
from app.services.csfloat_client import CSFloatClient
from app.services.item_manager import ItemManager
import logging

logger = logging.getLogger(__name__)


class PriceUpdater:
    """Service for updating item prices from various sources"""

    def __init__(self, db: Session):
        self.db = db
        self.csfloat = CSFloatClient()
        self.item_manager = ItemManager(db)

    def update_csfloat_prices(self):
        """
        Update CSFloat prices for ALL active items using bulk price-list endpoint
        Records DAILY candles (not hourly). Runs every 30 minutes but updates same-day candle.
        """
        logger.info("Starting CSFloat price update for all items")

        try:
            # Get full price list from CSFloat
            price_data = self.csfloat.get_price_list()
            
            if not price_data:
                logger.error("Failed to fetch CSFloat price list")
                return

            logger.info(f"Fetched {len(price_data)} items from CSFloat")

            # Create price map
            price_map = {item["market_hash_name"]: item for item in price_data}

            # Get all active items
            items = self.item_manager.get_all_active_items()
            
            if not items:
                logger.info("No active items to update")
                return

            updated_count = 0
            skipped_count = 0

            for item in items:
                try:
                    # Find price in the bulk data
                    price_info = price_map.get(item.market_hash_name)
                    
                    if not price_info:
                        skipped_count += 1
                        continue

                    # Convert to our format
                    formatted_price = {
                        'price': price_info['min_price'] / 100.0,  # cents to dollars
                        'volume': price_info.get('qty', 0),
                        'updated_at': datetime.utcnow()
                    }

                    # Update current price
                    self._update_item_price(item.id, 'csfloat', formatted_price)

                    # Record/update DAILY candle
                    self._record_daily_price(item.id, 'csfloat', formatted_price)

                    updated_count += 1

                    # Commit every 1000 items
                    if updated_count % 1000 == 0:
                        self.db.commit()
                        logger.info(f"Progress: {updated_count} updated, {skipped_count} skipped")

                except Exception as e:
                    logger.error(f"Failed to update price for {item.market_hash_name}: {e}")

            self.db.commit()
            logger.info(f"CSFloat update complete: {updated_count} updated, {skipped_count} skipped")

        except Exception as e:
            logger.error(f"CSFloat price update failed: {e}")
            self.db.rollback()
        finally:
            self.csfloat.close()

    def update_buff_prices(self):
        """Update Buff163 prices for all items"""
        logger.info("Buff price updates not yet implemented")
        pass

    def update_steam_prices(self):
        """Update Steam Market prices for all items (weekly reference)"""
        logger.info("Steam price updates not yet implemented")
        pass

    def _update_item_price(self, item_id: int, source: str, price_data: dict):
        """Update or create current price record for an item"""
        item_price = self.db.query(ItemPrice).filter(
            ItemPrice.item_id == item_id
        ).first()

        if not item_price:
            item_price = ItemPrice(item_id=item_id)
            self.db.add(item_price)

        # Update based on source
        if source == 'csfloat':
            item_price.csfloat_price = price_data.get('price')
            item_price.csfloat_volume = price_data.get('volume')
            item_price.csfloat_updated_at = price_data.get('updated_at', datetime.utcnow())
        elif source == 'buff':
            item_price.buff_price = price_data.get('price')
            item_price.buff_volume = price_data.get('volume')
            item_price.buff_updated_at = price_data.get('updated_at', datetime.utcnow())
        elif source == 'steam':
            item_price.steam_price = price_data.get('price')
            item_price.steam_volume = price_data.get('volume')
            item_price.steam_updated_at = price_data.get('updated_at', datetime.utcnow())

        item_price.last_updated = datetime.utcnow()

    def _record_daily_price(self, item_id: int, source: str, price_data: dict):
        """
        Record/update DAILY OHLC candle
        Multiple updates in same day will update the candle progressively
        """
        today = date.today()
        price = price_data.get('price')

        if not price:
            return

        # Check if we have a daily record for today
        existing = self.db.query(PriceHistory).filter(
            PriceHistory.item_id == item_id,
            PriceHistory.source == source,
            PriceHistory.date == today,
            PriceHistory.resolution == 'daily'
        ).first()

        if not existing:
            # Create new daily candle
            price_history = PriceHistory(
                item_id=item_id,
                source=source,
                date=today,
                resolution='daily',
                open_price=price,
                high_price=price,
                low_price=price,
                close_price=price,
                volume=price_data.get('volume', 0)
            )
            self.db.add(price_history)
        else:
            # Update existing daily OHLC candle
            existing.high_price = max(existing.high_price or price, price)
            existing.low_price = min(existing.low_price or price, price)
            existing.close_price = price  # Most recent price becomes close
            existing.volume = price_data.get('volume', 0)

    def compress_old_hourly_data(self):
        """
        DEPRECATED - We're now using daily candles directly
        This job can be removed or repurposed for other cleanup
        """
        logger.info("Hourly compression skipped - using daily candles directly")
        pass

    def get_price_history(self, item_id: int, source: str = 'csfloat', days: int = 30) -> List[PriceHistory]:
        """
        Get daily price history for an item

        Args:
            item_id: Item ID
            source: Price source
            days: Number of days of history

        Returns:
            List of daily PriceHistory records
        """
        cutoff_date = date.today() - timedelta(days=days)

        return self.db.query(PriceHistory).filter(
            PriceHistory.item_id == item_id,
            PriceHistory.source == source,
            PriceHistory.date >= cutoff_date,
            PriceHistory.resolution == 'daily'
        ).order_by(PriceHistory.date.asc()).all()
