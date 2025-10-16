import requests
import urllib.parse
from typing import Optional, Dict
from datetime import datetime
import time


class SteamMarketAPI:
    """
    Service for fetching prices from Steam Community Market
    """
    BASE_URL = "https://steamcommunity.com/market/priceoverview/"
    APP_ID = 730  # CS:GO/CS2 App ID

    def __init__(self):
        self.session = requests.Session()
        # Add headers to look more like a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self.last_request_time = 0
        self.rate_limit_delay = 3.0  # Increased to 3 seconds between requests

    def _rate_limit(self):
        """
        Enforce rate limiting to avoid being blocked by Steam

        :return: None
        """
        if self.last_request_time == 0:
            self.last_request_time = time.time()
            return

        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            print(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_item_price(self, item_name: str) -> Optional[Dict]:
        """
        Get current market price for an item from Steam Market

        :param item_name: (str) Full item name (e.g., "AK-47 | Redline (Field-Tested)")
        :return: (dict | None) Price data or None if not found
        """
        self._rate_limit()

        try:
            params = {
                'appid': self.APP_ID,
                'currency': 2,  # GBP
                'market_hash_name': item_name
            }

            print(f"Fetching price for: {item_name}")

            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=15  # Increased timeout
            )

            print(f"Response status: {response.status_code}")

            if response.status_code == 429:
                print("Rate limited by Steam! Waiting longer...")
                time.sleep(10)  # Wait 10 seconds if rate limited
                return None

            if response.status_code == 200:
                data = response.json()

                if data.get('success') and 'median_price' in data:
                    median_price_str = data['median_price'].replace('£', '').replace(',', '')
                    median_price = float(median_price_str)

                    print(f"Price found: £{median_price}")

                    return {
                        'price': median_price,
                        'currency': 'GBP',
                        'volume': data.get('volume', 'N/A'),
                        'timestamp': datetime.utcnow()
                    }
                else:
                    print(f"Item not found on market: {item_name}")

            return None

        except requests.exceptions.Timeout:
            print(f"Timeout fetching price for {item_name}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request error fetching price for {item_name}: {str(e)}")
            return None
        except Exception as e:
            print(f"Error fetching price for {item_name}: {str(e)}")
            return None

    def format_item_name_for_steam(self, item_name: str, item_type: str) -> str:
        """
        Format item name to match Steam Market naming convention

        :param item_name: (str) Item name from database
        :param item_type: (str) Item type (skin, sticker, etc.)
        :return: (str) Formatted name for Steam API
        """
        return item_name


# Create a singleton instance
steam_market_api = SteamMarketAPI()
