"""
PriceService — legacy compatibility wrapper.
New code should use price_updater.py, buff_client.py, steam_price_client.py directly.
This file kept to avoid breaking any remaining imports.
"""
import logging
from sqlalchemy.orm import Session
from app.services.price_updater import PriceUpdater

logger = logging.getLogger(__name__)


class PriceService:
    """Thin wrapper around PriceUpdater for backwards compatibility."""

    def __init__(self, db: Session):
        self.db = db
        self.updater = PriceUpdater(db)

    def update_all_prices_from_csfloat(self):
        return self.updater.update_csfloat_prices()

    def update_buff_prices(self):
        return self.updater.update_buff_prices()

    def update_steam_prices(self):
        return self.updater.update_steam_prices()
