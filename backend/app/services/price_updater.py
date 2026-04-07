"""
Price Updater — orchestrates price updates from all sources.
CSFloat: bulk price-list, every 30 minutes.
Buff/Steam: delegated to their dedicated clients.
All writes use V4 row-per-market item_prices structure.
"""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.item_price import ItemPrice
from app.models.price_update_log import PriceUpdateLog
from app.services.csfloat_client import CSFloatClient
from app.services.item_manager import ItemManager

logger = logging.getLogger(__name__)


class PriceUpdater:

    def __init__(self, db: Session):
        self.db = db
        self.csfloat = CSFloatClient()
        self.item_manager = ItemManager(db)

    def update_csfloat_prices(self):
        """Fetch CSFloat bulk price list and update item_prices (V4)."""
        logger.info("Starting CSFloat price update")
        start_time = datetime.utcnow()
        stats = {"updated": 0, "skipped": 0, "errors": 0}

        try:
            price_data = self.csfloat.get_price_list()
            if not price_data:
                logger.error("CSFloat returned empty price list")
                self._log("csfloat", stats, start_time, "failed", error="Empty price list")
                return

            logger.info(f"Fetched {len(price_data)} items from CSFloat")
            price_map = {item["market_hash_name"]: item for item in price_data}
            items = self.item_manager.get_all_active_items()
            now = datetime.utcnow()

            for item in items:
                try:
                    price_info = price_map.get(item.market_hash_name)
                    if not price_info:
                        stats["skipped"] += 1
                        continue

                    price = price_info["min_price"] / 100.0
                    volume = price_info.get("qty", 0)
                    self._upsert(item.id, "csfloat", price, volume, "USD", now)
                    stats["updated"] += 1

                    if stats["updated"] % 1000 == 0:
                        self.db.commit()
                        logger.info(f"CSFloat: {stats['updated']} updated, {stats['skipped']} skipped")

                except Exception as e:
                    logger.error(f"CSFloat price error for {item.market_hash_name}: {e}")
                    stats["errors"] += 1

            self.db.commit()
            duration = (datetime.utcnow() - start_time).seconds
            status = "success" if stats["errors"] == 0 else "partial"
            self._log("csfloat", stats, start_time, status, duration=duration)
            logger.info(f"CSFloat complete in {duration}s — {stats}")

        except Exception as e:
            logger.error(f"CSFloat update failed: {e}")
            self.db.rollback()
            self._log("csfloat", stats, start_time, "failed", error=str(e))
        finally:
            self.csfloat.close()

    def update_buff_prices(self):
        """Delegate to buff_client."""
        from app.services.buff_client import run_buff_price_update
        run_buff_price_update(self.db)

    def update_steam_prices(self):
        """Delegate to steam_price_client."""
        from app.services.steam_price_client import run_hourly_update
        run_hourly_update(self.db)

    def _upsert(
        self, item_id: int, market: str, price: float,
        volume: int, currency: str, now: datetime,
        lowest_listing: Optional[float] = None,
        highest_bid: Optional[float] = None,
    ):
        """Upsert a V4 item_prices row for (item_id, market)."""
        existing = self.db.query(ItemPrice).filter(
            ItemPrice.item_id == item_id,
            ItemPrice.market == market,
        ).first()

        if existing:
            existing.price = price
            existing.volume = volume
            existing.currency = currency
            existing.updated_at = now
            if lowest_listing is not None:
                existing.lowest_listing = lowest_listing
            if highest_bid is not None:
                existing.highest_bid = highest_bid
        else:
            self.db.add(ItemPrice(
                item_id=item_id, market=market, price=price,
                volume=volume, currency=currency,
                lowest_listing=lowest_listing, highest_bid=highest_bid,
                updated_at=now,
            ))

    def _log(self, market, stats, start_time, status, duration=0, error=None):
        try:
            self.db.add(PriceUpdateLog(
                market=market,
                items_updated=stats.get("updated", 0),
                items_failed=stats.get("errors", 0),
                items_skipped=stats.get("skipped", 0),
                duration_seconds=duration,
                ran_at=start_time,
                status=status,
                error_msg=error,
            ))
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to write price_update_log: {e}")
