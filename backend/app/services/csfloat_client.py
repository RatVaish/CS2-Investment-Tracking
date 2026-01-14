import httpx
import logging
from typing import Optional, Dict
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class CSFloatClient:
    """Client for interacting with CSFloat API"""

    BASE_URL = "https://csfloat.com/api/v1"

    def __init__(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://csfloat.com/',
            'Origin': 'https://csfloat.com'
        }
        self.client = httpx.Client(timeout=30.0, headers=headers, follow_redirects=True)

    def get_item_price(self, market_hash_name: str) -> Optional[Dict]:
        """
        Get reference price for an item from CSFloat.
        Uses the base_price from reference data, not individual listing prices.
        """
        try:
            time.sleep(1)  # Rate limiting

            response = self.client.get(
                f"{self.BASE_URL}/listings",
                params={
                    "market_hash_name": market_hash_name,
                    "limit": 1,  # We only need one listing to get reference data
                    "sort_by": "price",
                    "type": "buy_now"
                }
            )
            response.raise_for_status()
            data = response.json()

            if not data.get('data'):
                logger.warning(f"No listings found for {market_hash_name}")
                return None

            # Get first listing
            first_listing = data['data'][0]
            
            # Extract reference data (this is the market standard price)
            reference = first_listing.get('reference', {})
            
            if not reference:
                logger.warning(f"No reference data for {market_hash_name}")
                return None
            
            base_price = reference.get('base_price')
            quantity = reference.get('quantity', 0)
            last_updated_str = reference.get('last_updated')
            
            if base_price is None:
                logger.warning(f"No base_price in reference for {market_hash_name}")
                return None
            
            # Parse last_updated timestamp
            reference_updated_at = None
            if last_updated_str:
                try:
                    reference_updated_at = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                except Exception as e:
                    logger.warning(f"Could not parse last_updated: {e}")
            
            # Get actual listing price for comparison
            listing_price = first_listing.get('price', 0)
            
            return {
                "price": base_price / 100.0,  # Convert cents to dollars
                "volume": quantity,
                "lowest_listing": listing_price / 100.0,  # Actual cheapest listing
                "reference_updated_at": reference_updated_at,
                "updated_at": datetime.utcnow()
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.error(f"CSFloat blocked request (403) for {market_hash_name}")
            else:
                logger.error(f"CSFloat HTTP {e.response.status_code} for {market_hash_name}: {e}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"CSFloat network error for {market_hash_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {market_hash_name}: {e}")
            return None

    def close(self):
        """Close the HTTP client"""
        self.client.close()
