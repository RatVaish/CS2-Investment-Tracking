import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.item import Item
from app.models.item_price import ItemPrice
from app.models.price_history import PriceHistory
from app.services.csfloat_client import CSFloatClient

logger = logging.getLogger(__name__)

class PriceService:
    """Service for managing item prices from multiple sources"""
    
    def __init__(self, db: Session):
        self.db = db
        self.csfloat = CSFloatClient()
    
    def update_all_prices_from_csfloat(self) -> Dict[str, int]:
        """
        Fetch all prices from CSFloat price-list endpoint and update database.
        Returns: {"updated": count, "failed": count, "skipped": count}
        """
        stats = {"updated": 0, "failed": 0, "skipped": 0}
        
        try:
            # Get full price list from CSFloat
            price_data = self.csfloat.get_price_list()
            
            if not price_data:
                logger.error("Failed to fetch price list from CSFloat")
                return stats
            
            logger.info(f"Fetched {len(price_data)} items from CSFloat price list")
            
            # Create a map of market_hash_name -> price data
            price_map = {
                item["market_hash_name"]: item 
                for item in price_data
            }
            
            # Get all items from database
            items = self.db.query(Item).all()
            logger.info(f"Found {len(items)} items in database")
            
            for item in items:
                try:
                    # Find matching price data
                    price_info = price_map.get(item.market_hash_name)
                    
                    if not price_info:
                        stats["skipped"] += 1
                        continue
                    
                    # Convert cents to dollars
                    new_price = price_info["min_price"] / 100.0
                    new_volume = price_info.get("qty", 0)
                    
                    # Get or create ItemPrice record
                    item_price = self.db.query(ItemPrice).filter(
                        ItemPrice.item_id == item.id
                    ).first()
                    
                    if not item_price:
                        # Create new price record
                        item_price = ItemPrice(
                            item_id=item.id,
                            csfloat_price=new_price,
                            csfloat_volume=new_volume,
                            csfloat_updated_at=datetime.utcnow(),
                            last_updated=datetime.utcnow()
                        )
                        self.db.add(item_price)
                    else:
                        # Update existing price
                        old_price = item_price.csfloat_price
                        
                        # Only update if price changed significantly (> 1 cent)
                        if old_price is None or abs(old_price - new_price) > 0.01:
                            # Update hourly price history (for compression later)
                            self._update_hourly_history(
                                item.id, 
                                "csfloat", 
                                new_price, 
                                new_volume
                            )
                            
                            # Update current price
                            item_price.csfloat_price = new_price
                            item_price.csfloat_volume = new_volume
                            item_price.csfloat_updated_at = datetime.utcnow()
                            item_price.last_updated = datetime.utcnow()
                    
                    stats["updated"] += 1
                    
                    # Commit every 1000 items to avoid huge transactions
                    if stats["updated"] % 1000 == 0:
                        self.db.commit()
                        logger.info(f"Progress: {stats['updated']} updated, {stats['skipped']} skipped")
                    
                except Exception as e:
                    logger.error(f"Error updating price for {item.market_hash_name}: {e}")
                    stats["failed"] += 1
                    continue
            
            self.db.commit()
            logger.info(f"Price update complete: {stats}")
            
        except Exception as e:
            logger.error(f"Error in update_all_prices_from_csfloat: {e}")
            self.db.rollback()
            stats["failed"] += 1
        finally:
            self.csfloat.close()
        
        return stats
    
    def _update_hourly_history(self, item_id: int, source: str, price: float, volume: int):
        """Update hourly price history with OHLC data"""
        today = date.today()
        
        # Check if we have an hourly record for today
        history = self.db.query(PriceHistory).filter(
            PriceHistory.item_id == item_id,
            PriceHistory.source == source,
            PriceHistory.date == today,
            PriceHistory.resolution == 'hourly'
        ).first()
        
        if not history:
            # Create new hourly record
            history = PriceHistory(
                item_id=item_id,
                source=source,
                date=today,
                resolution='hourly',
                open_price=price,
                high_price=price,
                low_price=price,
                close_price=price,
                volume=volume
            )
            self.db.add(history)
        else:
            # Update existing record (OHLC)
            history.high_price = max(history.high_price or price, price)
            history.low_price = min(history.low_price or price, price)
            history.close_price = price
            history.volume = volume
    
    def get_item_current_price(self, item_id: int) -> Optional[float]:
        """Get current CSFloat price for a specific item"""
        item_price = self.db.query(ItemPrice).filter(
            ItemPrice.item_id == item_id
        ).first()
        
        return item_price.csfloat_price if item_price else None
    
    def get_item_price_history(
        self, 
        item_id: int, 
        days: int = 30,
        resolution: str = 'daily'
    ) -> List[Dict]:
        """Get price history for an item"""
        cutoff_date = date.today() - timedelta(days=days)
        
        history = self.db.query(PriceHistory).filter(
            PriceHistory.item_id == item_id,
            PriceHistory.date >= cutoff_date,
            PriceHistory.resolution == resolution
        ).order_by(PriceHistory.date).all()
        
        return [
            {
                "date": h.date.isoformat(),
                "open": h.open_price,
                "high": h.high_price,
                "low": h.low_price,
                "close": h.close_price,
                "volume": h.volume,
                "source": h.source
            }
            for h in history
        ]
