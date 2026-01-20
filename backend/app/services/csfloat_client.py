import httpx
import logging
from typing import Optional, Dict
from datetime import datetime
import time
from app.core.config import settings

logger = logging.getLogger(__name__)

class CSFloatClient:
    """Client for interacting with CSFloat API"""

    BASE_URL = "https://csfloat.com/api/v1"

    def __init__(self):
        if not settings.CSFLOAT_API_KEY:
            raise ValueError("CSFLOAT_API_KEY not found in environment variables")
        
        headers = {
            'Authorization': settings.CSFLOAT_API_KEY,  # Just the raw key, no Bearer
            'User-Agent': 'CS2InvestmentTracker/1.0'
        }
        self.client = httpx.Client(timeout=30.0, headers=headers, follow_redirects=True)

    def get_item_price(self, market_hash_name: str) -> Optional[Dict]:
        """
        Get reference price for an item from CSFloat.
        Uses the base_price from reference data.
        """
        try:
            time.sleep(1)  # Rate limiting

            response = self.client.get(
                f"{self.BASE_URL}/listings",
                params={
                    "market_hash_name": market_hash_name,
                    "limit": 1,
                    "sort_by": "lowest_price",
                    "type": "buy_now"
                }
            )
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list) or not data:
                logger.warning(f"No listings found for {market_hash_name}")
                return None

            # Get first listing
            first_listing = data[0]
            item = first_listing.get('item', {})
            
            # Get listing price
            listing_price = first_listing.get('price', 0)
            
            # Try to get Steam Community Market data if available
            scm = item.get('scm', {})
            scm_price = scm.get('price', 0) if scm else 0
            
            return {
                "price": listing_price / 100.0,  # Convert cents to dollars
                "scm_price": scm_price / 100.0 if scm_price else None,
                "float_value": item.get('float_value'),
                "market_hash_name": item.get('market_hash_name'),
                "updated_at": datetime.utcnow()
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error(f"CSFloat authentication failed - check API key")
            elif e.response.status_code == 403:
                logger.error(f"CSFloat access forbidden for {market_hash_name}")
            elif e.response.status_code == 404:
                logger.error(f"CSFloat endpoint not found - URL might be incorrect")
            else:
                logger.error(f"CSFloat HTTP {e.response.status_code} for {market_hash_name}: {e}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"CSFloat network error for {market_hash_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {market_hash_name}: {e}")
            return None

    def get_price_list(self) -> Optional[Dict]:
        """
        Get the full price list from CSFloat.
        This might be better for bulk price updates.
        """
        try:
            response = self.client.get(f"{self.BASE_URL}/listings/price-list")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching price list: {e}")
            return None

    def close(self):
        """Close the HTTP client"""
        self.client.close()
