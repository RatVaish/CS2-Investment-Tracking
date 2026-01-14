import httpx
import logging
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class CSFloatClient:
    """Client for interacting with CSFloat API"""

    BASE_URL = "https://csfloat.com/api/v1"

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)

    def get_item_price(self, market_hash_name: str) -> Optional[Dict]:
        """
        Get current price for a specific item

        Args:
            market_hash_name: Full item name (e.g., "AK-47 | Redline (Field-Tested)")

        Returns:
            Dict with price data or None if not found
        """
        try:
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
                "price": min(prices) / 100,  # Convert cents to dollars
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

    def search_items(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for items by name

        Args:
            query: Search query (e.g., "howl", "ak redline")
            limit: Max number of results

        Returns:
            List of item dictionaries
        """
        try:
            response = self.client.get(
                f"{self.BASE_URL}/listings",
                params={
                    "limit": limit,
                    "sort_by": "created_at"
                }
            )
            response.raise_for_status()
            data = response.json()

            items = []
            seen = set()

            for listing in data.get('data', []):
                item = listing.get('item', {})
                name = item.get('market_hash_name')

                # Filter by query and deduplicate
                if name and query.lower() in name.lower() and name not in seen:
                    items.append({
                        "market_hash_name": name,
                        "image_url": item.get('icon_url'),
                        "price": listing.get('price', 0) / 100
                    })
                    seen.add(name)

                    if len(items) >= limit:
                        break

            return items

        except Exception as e:
            logger.error(f"Error searching items: {e}")
            return []

    def get_all_items(self, batch_size: int = 100) -> List[Dict]:
        """
        Fetch all available items from CSFloat (for initial population)
        This is a slow operation - use for one-time backfill only

        Args:
            batch_size: Items per request

        Returns:
            List of all items
        """
        all_items = []
        seen = set()
        offset = 0

        logger.info("Starting to fetch all items from CSFloat...")

        while True:
            try:
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

                # Stop if we got less than batch_size (last page)
                if len(listings) < batch_size:
                    break

            except Exception as e:
                logger.error(f"Error fetching items at offset {offset}: {e}")
                break

        logger.info(f"Finished fetching {len(all_items)} total items")
        return all_items

    def close(self):
        """Close the HTTP client"""
        self.client.close()
        