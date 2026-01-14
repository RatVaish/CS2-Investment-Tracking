import httpx
import logging
from typing import Optional, Dict, List
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class CSFloatClient:
    """Client for interacting with CSFloat API"""
    
    BASE_URL = "https://csfloat.com/api/v1"
    
    def __init__(self):
        # Add browser-like headers to avoid 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://csfloat.com/',
            'Origin': 'https://csfloat.com'
        }
        self.client = httpx.Client(timeout=30.0, headers=headers, follow_redirects=True)
    
    def get_item_price(self, market_hash_name: str) -> Optional[Dict]:
        """Get current price for a specific item"""
        try:
            # Add delay to be respectful
            time.sleep(1)
            
            response = self.client.get(
                f"{self.BASE_URL}/listings",
                params={
                    "market_hash_name": market_hash_name,
                    "limit": 10,
                    "sort_by": "price",
                    "type": "buy_now"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('data'):
                logger.warning(f"No listings found for {market_hash_name}")
                return None
            
            listings = data['data']
            prices = [listing['price'] for listing in listings]
            
            return {
                "price": min(prices) / 100,
                "average_price": sum(prices) / len(prices) / 100,
                "volume": len(listings),
                "lowest_listing": min(prices) / 100,
                "updated_at": datetime.utcnow()
            }
            
        except httpx.HTTPError as e:
            logger.error(f"CSFloat API error for {market_hash_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {market_hash_name}: {e}")
            return None
    
    def get_all_items(self, batch_size: int = 50) -> List[Dict]:
        """Fetch all available items from CSFloat"""
        all_items = []
        seen = set()
        offset = 0
        
        logger.info("Starting to fetch all items from CSFloat...")
        
        while True:
            try:
                # Be respectful - add delay between requests
                time.sleep(2)
                
                response = self.client.get(
                    f"{self.BASE_URL}/listings",
                    params={
                        "limit": batch_size,
                        "offset": offset,
                        "sort_by": "created_at"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                listings = data.get('data', [])
                if not listings:
                    break
                
                for listing in listings:
                    item = listing.get('item', {})
                    name = item.get('market_hash_name')
                    
                    if name and name not in seen:
                        all_items.append({
                            "market_hash_name": name,
                            "image_url": item.get('icon_url')
                        })
                        seen.add(name)
                
                logger.info(f"Fetched {len(all_items)} unique items so far...")
                offset += batch_size
                
                # Stop if we got less than batch_size
                if len(listings) < batch_size:
                    break
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    logger.error("CSFloat is blocking requests (403). Try again later or use alternative source.")
                    break
                logger.error(f"HTTP error fetching items at offset {offset}: {e}")
                break
            except Exception as e:
                logger.error(f"Error fetching items at offset {offset}: {e}")
                break
        
        logger.info(f"Finished fetching {len(all_items)} total items")
        return all_items
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()
