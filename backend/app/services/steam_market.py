import requests
import urllib.parse
from typing import Optional, Dict
from datetime import datetime
import time

class SteamMarketAPI:
    """
    Service to fetch prices from teh Steam community market
    """
    BASE_URL = 'https://steamcommunity.com/market/priceoverview/'
    APP_ID = 730

    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_delay = 1.5

    def _rate_limit(self):
        """
        Enforce rate limit
        :return:
        """
        if self.last_request_time == 0:
            # First request, no need to wait
            self.last_request_time = time.time()
            return

        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_item_price(self, item_name: str) -> Optional[Dict]:
        """
        Get current market price from the steam market
        :param item_name: (str) Full item name
        :return: (dict | None) Price data or None if not found
        """

        self._rate_limit()

        try:
            params =  {
                'appid': self.APP_ID,
                "currency": 2,
                "market_hash_name": item_name
            }

            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                if data.get("success") and "median_price" in data:
                    median_price_str = data["median_price"].replace("£", "").replace(",", "")
                    median_price = float(median_price_str)

                    return {
                        "price": median_price,
                        "currency": "GBP",
                        "volume": data.get("volume", "N/A"),
                        "timestamp": datetime.utcnow()
                    }
            return None

        except Exception as e:
            print(f"Error fetching price for {item_name}: {str(e)}")
            return None

    def format_item_name_for_steam(self, item_name: str, item_type: str) -> str:
        """
        Format item name to match steam naming convention
        :param self:
        :param item_name: (str) Full item name
        :param item_type: (str) Item type
        :return: (str) Formatted name for SteamAPI
        """

        return item_name

steam_market_api = SteamMarketAPI()
