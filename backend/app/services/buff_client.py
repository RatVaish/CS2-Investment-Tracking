"""
Buff163 Price Client

Fetches current CS2 item prices from Buff163's market goods endpoint.
Buff prices are in CNY (Chinese Yuan).

Endpoint:
    GET https://buff.163.com/api/market/goods
        ?game=csgo
        &page_num={page}
        &page_size=80

Response per item:
    {
        "id": 968401,                          <- Buff goods_id
        "market_hash_name": "UMP-45 | ...",
        "sell_min_price": "355.49",            <- lowest listing (CNY)
        "buy_max_price": "327",                <- highest buy order (CNY)
        "sell_num": 69,                        <- active listings count
        "buy_num": 19,                         <- active buy orders count
        "goods_info": {
            "steam_price": "65.72",            <- Steam price USD (bonus)
        }
    }

Strategy:
    - Daily full crawl of all ~350 pages
    - Updates item_prices table with current CNY price
    - Updates today's daily candle in price_history
    - Does NOT attempt hourly candles (Steam handles real trade history)
    - Buff prices serve as current CNY reference price overlay on charts
"""

import time
import logging
import requests
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.item import Item
from app.models.item_price import ItemPrice
from app.models.price_history import PriceHistory
from app.models.price_update_log import PriceUpdateLog

logger = logging.getLogger(__name__)

BUFF_GOODS_URL = "https://buff.163.com/api/market/goods"
PAGE_SIZE = 80
REQUEST_DELAY = 2.0  # seconds between pages


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

def make_session() -> requests.Session:
    """Create authenticated Buff session."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://buff.163.com/market/",
    })
    if settings.BUFF_SESSION_COOKIE:
        session.cookies.set(
            "session",
            settings.BUFF_SESSION_COOKIE,
            domain="buff.163.com"
        )
    return session


# ---------------------------------------------------------------------------
# Fetch all Buff goods
# ---------------------------------------------------------------------------

def fetch_page(page_num: int, session: requests.Session) -> Optional[dict]:
    """Fetch one page of Buff market goods."""
    try:
        response = session.get(
            BUFF_GOODS_URL,
            params={
                "game": "csgo",
                "page_num": page_num,
                "page_size": PAGE_SIZE,
            },
            timeout=20,
        )

        if response.status_code == 429:
            logger.warning(f"Rate limited at page {page_num}. Waiting 60s...")
            time.sleep(60)
            response = session.get(
                BUFF_GOODS_URL,
                params={"game": "csgo", "page_num": page_num, "page_size": PAGE_SIZE},
                timeout=20,
            )

        response.raise_for_status()
        data = response.json()

        if data.get("code") != "OK":
            if data.get("code") == "Login Required":
                logger.error("Buff session cookie expired — update BUFF_SESSION_COOKIE in .env")
            else:
                logger.error(f"Buff returned code={data.get('code')} on page {page_num}")
            return None

        return data

    except requests.exceptions.Timeout:
        logger.error(f"Timeout on Buff page {page_num}")
        return None
    except Exception as e:
        logger.error(f"Error fetching Buff page {page_num}: {e}")
        return None


def fetch_all_buff_prices() -> dict:
    """
    Paginate through all Buff CS2 goods.

    Returns dict keyed by market_hash_name:
    {
        "AK-47 | Redline (Field-Tested)": {
            "buff_id": 968401,
            "price": 355.49,
            "buy_max_price": 327.0,
            "sell_num": 69,
            "buy_num": 19,
        },
        ...
    }
    """
    session = make_session()

    # First page to get total count
    first_page = fetch_page(1, session)
    if not first_page:
        logger.error("Failed to fetch first Buff page")
        return {}

    d = first_page["data"]
    total_page = d.get("total_page", 1)
    total_count = d.get("total_count", 0)
    logger.info(f"Buff reports {total_count} items across {total_page} pages")

    price_map = {}

    def process_page(data: dict):
        items = data["data"].get("items", [])
        for item in items:
            mhn = item.get("market_hash_name")
            if not mhn:
                continue
            try:
                price_map[mhn] = {
                    "buff_id": item.get("id"),
                    "price": float(item.get("sell_min_price", 0)),
                    "buy_max_price": float(item.get("buy_max_price", 0)),
                    "sell_num": int(item.get("sell_num", 0)),
                    "buy_num": int(item.get("buy_num", 0)),
                }
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse Buff item {mhn}: {e}")

    process_page(first_page)

    for page_num in range(2, total_page + 1):
        time.sleep(REQUEST_DELAY)
        data = fetch_page(page_num, session)
        if data:
            process_page(data)
        else:
            logger.warning(f"Skipping Buff page {page_num}")

        if page_num % 50 == 0:
            logger.info(f"Buff crawl progress: page {page_num}/{total_page} ({len(price_map)} items)")

    logger.info(f"Buff crawl complete: {len(price_map)} items fetched")
    return price_map


# ---------------------------------------------------------------------------
# DB writes
# ---------------------------------------------------------------------------

def update_buff_prices(db: Session, price_map: dict) -> dict:
    """
    Update item_prices and price_history for all items with Buff data.

    Matches Buff items to our items table by market_hash_name.
    Updates:
        - item_prices (market='buff163') with current CNY price
        - price_history daily candle for today
    """
    now = datetime.utcnow()
    today_ts = now.replace(hour=0, minute=0, second=0, microsecond=0)
    stats = {"updated": 0, "not_found": 0, "errors": 0}

    # Load all items into memory for fast lookup
    items_by_name = {
        item.market_hash_name: item
        for item in db.query(Item).filter(Item.is_active == True).all()
    }

    batch_count = 0

    for mhn, buff_data in price_map.items():
        item = items_by_name.get(mhn)
        if not item:
            stats["not_found"] += 1
            continue

        try:
            price = buff_data["price"]
            if price <= 0:
                continue

            # ----------------------------------------------------------------
            # Update item_prices (current price)
            # ----------------------------------------------------------------
            existing_price = db.query(ItemPrice).filter(
                ItemPrice.item_id == item.id,
                ItemPrice.market == "buff163",
            ).first()

            if existing_price:
                existing_price.price = price
                existing_price.lowest_listing = price
                existing_price.highest_bid = buff_data["buy_max_price"]
                existing_price.volume = buff_data["sell_num"]
                existing_price.listing_count = buff_data["sell_num"]
                existing_price.updated_at = now
            else:
                db.add(ItemPrice(
                    item_id=item.id,
                    market="buff163",
                    price=price,
                    lowest_listing=price,
                    highest_bid=buff_data["buy_max_price"],
                    volume=buff_data["sell_num"],
                    listing_count=buff_data["sell_num"],
                    currency="CNY",
                    updated_at=now,
                ))

            # ----------------------------------------------------------------
            # Update today's daily candle in price_history
            # ----------------------------------------------------------------
            existing_candle = db.query(PriceHistory).filter(
                PriceHistory.item_id == item.id,
                PriceHistory.market == "buff163",
                PriceHistory.resolution == "daily",
                PriceHistory.candle_timestamp == today_ts,
            ).first()

            if existing_candle:
                # Update candle — high/low track intraday movement
                existing_candle.high_price = max(existing_candle.high_price or price, price)
                existing_candle.low_price = min(existing_candle.low_price or price, price)
                existing_candle.close_price = price
                existing_candle.volume = buff_data["sell_num"]
                existing_candle.updated_at = now
            else:
                # New candle for today
                db.add(PriceHistory(
                    item_id=item.id,
                    market="buff163",
                    resolution="daily",
                    candle_timestamp=today_ts,
                    open_price=price,
                    high_price=price,
                    low_price=price,
                    close_price=price,
                    volume=buff_data["sell_num"],
                    currency="CNY",
                ))

            stats["updated"] += 1
            batch_count += 1

            if batch_count % 1000 == 0:
                db.commit()
                logger.info(f"Written {batch_count} Buff price updates...")

        except Exception as e:
            logger.error(f"Error writing Buff data for {mhn}: {e}")
            stats["errors"] += 1

    db.commit()
    return stats


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_buff_price_update(db: Session) -> dict:
    """
    Full Buff price update job.
    Called daily by the scheduler.

    1. Crawl all ~350 Buff pages (~10-15 minutes)
    2. Update item_prices for all matched items
    3. Update today's daily candle in price_history
    4. Log result to price_update_log
    """
    logger.info("Starting Buff163 daily price update...")
    start_time = datetime.utcnow()

    if not settings.BUFF_SESSION_COOKIE:
        logger.error("BUFF_SESSION_COOKIE not set — skipping Buff update")
        return {"status": "failed", "error": "No session cookie"}

    try:
        price_map = fetch_all_buff_prices()

        if not price_map:
            log = PriceUpdateLog(
                market="buff163",
                status="failed",
                error_msg="fetch_all_buff_prices returned empty",
                ran_at=start_time,
            )
            db.add(log)
            db.commit()
            return {"status": "failed"}

        stats = update_buff_prices(db, price_map)
        duration = (datetime.utcnow() - start_time).seconds
        status = "success" if stats["errors"] == 0 else "partial"

        log = PriceUpdateLog(
            market="buff163",
            items_updated=stats["updated"],
            items_failed=stats["errors"],
            items_skipped=stats["not_found"],
            duration_seconds=duration,
            ran_at=start_time,
            status=status,
            error_msg=f"{stats['errors']} errors" if stats["errors"] else None,
        )
        db.add(log)
        db.commit()

        logger.info(
            f"Buff update complete in {duration}s — "
            f"updated={stats['updated']} not_found={stats['not_found']} errors={stats['errors']}"
        )
        return {"status": status, **stats}

    except Exception as e:
        logger.error(f"Buff update failed: {e}")
        log = PriceUpdateLog(
            market="buff163",
            status="failed",
            error_msg=str(e),
            ran_at=start_time,
        )
        db.add(log)
        db.commit()
        return {"status": "failed", "error": str(e)}
