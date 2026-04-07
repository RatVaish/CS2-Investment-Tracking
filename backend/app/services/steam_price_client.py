"""
Steam Market Price History Client

Fetches real completed sale data from Steam's price history endpoint.
This is actual transaction data (median price + volume per hour/day),
not order book snapshots.

Endpoint:
    GET https://steamcommunity.com/market/pricehistory/
        ?appid=730
        &market_hash_name={name}

Response:
    {
        "success": true,
        "prices": [
            ["Feb 21 2014 01: +0", 31.351, "198"],  <- [datetime_str, median_price_usd, volume]
            ["Feb 21 2014 02: +0", 30.12,  "145"],
            ...
        ]
    }

Steam automatically returns:
    - Hourly data for recent entries (last ~3 months)
    - Daily data for older entries

We aggregate these raw data points into OHLV candles:
    - hourly resolution: last 30 days
    - daily resolution:  30 days to 1 year
    - weekly resolution: older than 1 year
"""

import time
import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional
from collections import defaultdict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.item import Item
from app.models.item_price import ItemPrice
from app.models.price_history import PriceHistory

logger = logging.getLogger(__name__)

STEAM_HISTORY_URL = "https://steamcommunity.com/market/pricehistory/"
REQUEST_DELAY = 1.5   # seconds between requests — Steam rate limits aggressively

# Resolution thresholds
HOURLY_CUTOFF_DAYS = 30     # last 30 days → hourly candles
DAILY_CUTOFF_DAYS = 365     # 30 days to 1 year → daily candles
# older than 365 days → weekly candles


# ---------------------------------------------------------------------------
# Raw data fetching
# ---------------------------------------------------------------------------

def make_session() -> requests.Session:
    """Create authenticated Steam session."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://steamcommunity.com/market/",
    })
    if settings.STEAM_LOGIN_SECURE:
        session.cookies.set(
            "steamLoginSecure",
            settings.STEAM_LOGIN_SECURE,
            domain="steamcommunity.com"
        )
    return session


def parse_steam_datetime(dt_str: str) -> Optional[datetime]:
    """
    Parse Steam's datetime format: "Apr 05 2026 14: +0"
    Returns UTC datetime at start of that hour.
    """
    try:
        # Remove trailing ": +0" and parse
        clean = dt_str.replace(": +0", "").strip()
        return datetime.strptime(clean, "%b %d %Y %H").replace(tzinfo=timezone.utc)
    except Exception as e:
        logger.warning(f"Failed to parse Steam datetime '{dt_str}': {e}")
        return None


def fetch_item_price_history(
    market_hash_name: str,
    session: requests.Session
) -> list:
    """
    Fetch raw price history from Steam for one item.

    Returns list of (datetime, price, volume) tuples sorted oldest first.
    Returns empty list on failure.
    """
    try:
        response = session.get(
            STEAM_HISTORY_URL,
            params={
                "appid": 730,
                "market_hash_name": market_hash_name,
            },
            timeout=15,
        )

        if response.status_code == 429:
            logger.warning(f"Rate limited fetching {market_hash_name}. Waiting 60s...")
            time.sleep(60)
            response = session.get(
                STEAM_HISTORY_URL,
                params={"appid": 730, "market_hash_name": market_hash_name},
                timeout=15,
            )

        if response.status_code == 400:
            # Item has no Steam Market history (too new, delisted, etc.)
            return []

        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            logger.warning(f"Steam returned success=false for {market_hash_name}")
            return []

        raw_prices = data.get("prices", [])
        result = []

        for entry in raw_prices:
            if len(entry) < 3:
                continue
            dt = parse_steam_datetime(entry[0])
            if not dt:
                continue
            try:
                price = float(entry[1])
                volume = int(entry[2])
                result.append((dt, price, volume))
            except (ValueError, TypeError):
                continue

        return sorted(result, key=lambda x: x[0])

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching history for {market_hash_name}")
        return []
    except Exception as e:
        logger.error(f"Error fetching history for {market_hash_name}: {e}")
        return []


# ---------------------------------------------------------------------------
# Candle aggregation
# ---------------------------------------------------------------------------

def get_resolution(dt: datetime, now: datetime) -> str:
    """Determine candle resolution based on age of data point."""
    age_days = (now - dt.replace(tzinfo=None)).days
    if age_days <= HOURLY_CUTOFF_DAYS:
        return "hourly"
    elif age_days <= DAILY_CUTOFF_DAYS:
        return "daily"
    else:
        return "weekly"


def get_candle_timestamp(dt: datetime, resolution: str) -> datetime:
    """
    Get the start timestamp of the candle period this datetime belongs to.

    hourly: truncate to hour  → 2026-04-05 14:00:00
    daily:  truncate to day   → 2026-04-05 00:00:00
    weekly: truncate to Monday → 2026-03-30 00:00:00
    """
    dt = dt.replace(tzinfo=None)  # strip timezone for DB storage
    if resolution == "hourly":
        return dt.replace(minute=0, second=0, microsecond=0)
    elif resolution == "daily":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif resolution == "weekly":
        # Roll back to Monday
        days_since_monday = dt.weekday()
        monday = dt - timedelta(days=days_since_monday)
        return monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return dt


def build_candles(raw_data: list, now: datetime) -> dict:
    """
    Aggregate raw Steam data points into OHLV candles.

    Args:
        raw_data: list of (datetime, price, volume) tuples
        now: current datetime for age calculation

    Returns:
        dict keyed by (candle_timestamp, resolution) →
        {open, high, low, close, volume}
    """
    # Group data points by candle bucket
    buckets = defaultdict(list)

    for dt, price, volume in raw_data:
        resolution = get_resolution(dt, now)
        candle_ts = get_candle_timestamp(dt, resolution)
        buckets[(candle_ts, resolution)].append((dt, price, volume))

    # Build OHLV for each bucket
    candles = {}
    for (candle_ts, resolution), points in buckets.items():
        points_sorted = sorted(points, key=lambda x: x[0])
        prices = [p[1] for p in points_sorted]
        volumes = [p[2] for p in points_sorted]

        candles[(candle_ts, resolution)] = {
            "open_price": prices[0],
            "high_price": max(prices),
            "low_price": min(prices),
            "close_price": prices[-1],
            "volume": sum(volumes),
        }

    return candles


# ---------------------------------------------------------------------------
# Anomaly filtering
# ---------------------------------------------------------------------------

def is_anomalous(price: float, prev_close: Optional[float], threshold: float = 0.8) -> bool:
    """
    Detect anomalous price data points.

    A price is anomalous if it deviates more than `threshold` (80%) from
    the previous close. This catches data errors without filtering
    legitimate large price movements (which do happen in CS2).

    80% threshold is intentionally loose — CS2 items can spike 50%+ on
    case openings or game updates. We only want to catch clear errors.
    """
    if prev_close is None or prev_close <= 0:
        return False
    deviation = abs(price - prev_close) / prev_close
    return deviation > threshold


# ---------------------------------------------------------------------------
# DB upsert
# ---------------------------------------------------------------------------

def upsert_candles(
    db: Session,
    item_id: int,
    market: str,
    candles: dict,
    currency: str = "USD"
) -> dict:
    """
    Upsert OHLV candles into price_history.

    For existing candles: update high/low/close/volume (open stays fixed).
    For new candles: insert.

    Returns stats dict.
    """
    stats = {"inserted": 0, "updated": 0}

    # Load existing candles for this item+market into memory
    existing = {}
    rows = db.query(PriceHistory).filter(
        PriceHistory.item_id == item_id,
        PriceHistory.market == market,
    ).all()
    for row in rows:
        existing[(row.candle_timestamp, row.resolution)] = row

    now = datetime.utcnow()

    sorted_candles = sorted(candles.items(), key=lambda x: x[0][0])

    for (candle_ts, resolution), data in sorted_candles:
        key = (candle_ts, resolution)

        if key in existing:
            row = existing[key]
            # Update: high/low/close/volume can change, open is fixed
            row.high_price = max(row.high_price or 0, data["high_price"])
            row.low_price = min(row.low_price or float("inf"), data["low_price"])
            row.close_price = data["close_price"]
            row.volume = data["volume"]
            row.updated_at = now
            stats["updated"] += 1
        else:
            row = PriceHistory(
                item_id=item_id,
                market=market,
                resolution=resolution,
                candle_timestamp=candle_ts,
                open_price=data["open_price"],
                high_price=data["high_price"],
                low_price=data["low_price"],
                close_price=data["close_price"],
                volume=data["volume"],
                currency=currency,
            )
            db.add(row)
            stats["inserted"] += 1

    db.commit()
    return stats


def update_current_price(
    db: Session,
    item_id: int,
    market: str,
    price: float,
    volume: int,
    currency: str = "USD"
):
    """
    Update the current price in item_prices table.
    Called after each successful history fetch.
    """
    from datetime import datetime
    now = datetime.utcnow()

    existing = db.query(ItemPrice).filter(
        ItemPrice.item_id == item_id,
        ItemPrice.market == market,
    ).first()

    if existing:
        existing.price = price
        existing.volume = volume
        existing.updated_at = now
    else:
        row = ItemPrice(
            item_id=item_id,
            market=market,
            price=price,
            volume=volume,
            currency=currency,
            updated_at=now,
        )
        db.add(row)

    db.commit()


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def process_item(
    db: Session,
    item: Item,
    session: requests.Session,
    now: datetime,
) -> dict:
    """
    Fetch Steam price history for one item and upsert candles.
    Sets item.last_synced_at so the hourly job picks it up going forward.
    Returns stats dict.
    """
    raw_data = fetch_item_price_history(item.market_hash_name, session)

    if not raw_data:
        return {"inserted": 0, "updated": 0, "no_data": True}

    candles = build_candles(raw_data, now)
    stats = upsert_candles(db, item.id, "steam", candles)

    # Update current price from most recent data point
    latest_dt, latest_price, latest_volume = raw_data[-1]
    update_current_price(db, item.id, "steam", latest_price, latest_volume)

    # Register item for hourly updates
    item.last_synced_at = now
    db.commit()

    stats["no_data"] = False
    return stats


def run_backfill(
    db: Session,
    batch_size: int = 50,
    delay_between_items: float = REQUEST_DELAY,
    item_type_filter: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """
    Backfill Steam price history for all items (or filtered subset).

    Designed to run as a background job over several days.
    Processes items in batches, sleeping between each to avoid rate limits.

    Args:
        db:                   SQLAlchemy session
        batch_size:           commit to DB every N items
        delay_between_items:  seconds between API calls
        item_type_filter:     e.g. 'case' to only backfill cases first
        limit:                max items to process (for testing)

    Usage:
        # Backfill all cases first (fast, ~475 items)
        run_backfill(db, item_type_filter='case')

        # Then backfill everything else
        run_backfill(db)
    """
    logger.info(f"Starting Steam price history backfill (filter={item_type_filter}, limit={limit})")
    now = datetime.utcnow()
    session = make_session()

    # Query items that haven't been synced yet
    # (last_synced_at is null or older than 7 days)
    query = db.query(Item).filter(Item.is_active == True)

    if item_type_filter:
        query = query.filter(Item.item_type == item_type_filter)

    # Prioritise items with no history yet
    # Items already in price_history are skipped if recently synced
    items = query.order_by(Item.id.asc()).all()

    if limit:
        items = items[:limit]

    logger.info(f"Processing {len(items)} items")

    total_stats = {
        "processed": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "no_data": 0,
        "errors": 0,
    }

    for i, item in enumerate(items):
        try:
            stats = process_item(db, item, session, now)

            total_stats["processed"] += 1
            total_stats["inserted"] += stats.get("inserted", 0)
            total_stats["updated"] += stats.get("updated", 0)
            total_stats["skipped"] += stats.get("skipped", 0)
            if stats.get("no_data"):
                total_stats["no_data"] += 1

            # Update last_synced_at on item
            item.last_synced_at = now
            if i % batch_size == 0:
                db.commit()
                logger.info(
                    f"Progress: {i+1}/{len(items)} items | "
                    f"inserted={total_stats['inserted']} "
                    f"updated={total_stats['updated']} "
                    f"no_data={total_stats['no_data']}"
                )

            time.sleep(delay_between_items)

        except Exception as e:
            logger.error(f"Error processing {item.market_hash_name}: {e}")
            total_stats["errors"] += 1
            time.sleep(delay_between_items)

    db.commit()
    logger.info(f"Backfill complete: {total_stats}")
    return total_stats


def run_hourly_update(db: Session) -> dict:
    """
    Hourly job — fetch latest Steam price history for tracked items only.

    Only processes items where last_synced_at IS NOT NULL,
    meaning they've been viewed at least once and have existing candle data.
    New items get added to tracking automatically when a user first opens them
    via the on-demand backfill in the price-history endpoint.
    """
    logger.info("Starting hourly Steam price history update")
    now = datetime.utcnow()
    session = make_session()

    # Only update items that have been synced before (tracked items)
    items = db.query(Item).filter(
        Item.is_active == True,
        Item.last_synced_at.isnot(None),
    ).all()

    logger.info(f"Updating {len(items)} tracked items")

    total_stats = {
        "processed": 0,
        "inserted": 0,
        "updated": 0,
        "errors": 0,
    }

    for i, item in enumerate(items):
        try:
            stats = process_item(db, item, session, now)
            total_stats["processed"] += 1
            total_stats["inserted"] += stats.get("inserted", 0)
            total_stats["updated"] += stats.get("updated", 0)

            # Update last_synced_at so we know when this item was last topped up
            item.last_synced_at = now
            if i % 100 == 0:
                db.commit()

            if i % 500 == 0 and i > 0:
                logger.info(
                    f"Progress: {i}/{len(items)} | "
                    f"inserted={total_stats['inserted']} "
                    f"updated={total_stats['updated']}"
                )

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            logger.error(f"Error updating {item.market_hash_name}: {e}")
            total_stats["errors"] += 1
            time.sleep(REQUEST_DELAY)

    db.commit()
    logger.info(f"Hourly update complete: {total_stats}")
    return total_stats
