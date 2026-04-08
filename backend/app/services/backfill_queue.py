"""
Backfill Queue Service

Decouples Steam price history fetching from the request cycle.

Flow:
  1. User adds investment → queue_item_for_backfill() sets needs_backfill=True
  2. Scheduler calls run_backfill_queue() every 2 minutes
  3. Queue worker fetches one item at a time with proper delays
  4. On rate limit: sleeps and retries — never marks done unless candles written
  5. After MAX_ATTEMPTS: gives up on that item (logs error, clears flag)
     so a broken item doesn't block the whole queue forever

Intentionally single-threaded and slow — Steam rate limits hard.
"""

import time
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.price_history import PriceHistory

logger = logging.getLogger(__name__)

DELAY_BETWEEN_ITEMS = 2.0    # seconds between successful fetches
RATE_LIMIT_BACKOFF  = 90     # seconds to sleep when Steam 429s us
MAX_ATTEMPTS        = 5      # give up after this many failed attempts per item


def _run_snapshot_backfill_for_user(user_id: int, item_id: int):
    """Background thread helper — runs snapshot backfill when price history already exists."""
    from app.db.session import SessionLocal
    from app.services.snapshot_backfill import backfill_snapshots_for_user
    db = SessionLocal()
    try:
        result = backfill_snapshots_for_user(db, user_id)
        logger.info(f"Snapshot backfill (existing history) for user {user_id}: {result}")
    except Exception as e:
        logger.error(f"Snapshot backfill thread failed for user {user_id}: {e}")
    finally:
        db.close()


def queue_item_for_backfill(db: Session, item_id: int, user_id: int = None) -> bool:
    """
    Mark an item as needing backfill. Called when a user adds an investment
    for an item that has no Steam price history yet.
    Idempotent — safe to call multiple times.
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return False

    # Check if history already exists
    existing = db.query(PriceHistory).filter(
        PriceHistory.item_id == item_id,
        PriceHistory.market == 'steam',
    ).first()

    if existing:
        # Price history already exists — no Steam fetch needed
        # but still trigger snapshot backfill for this user directly
        try:
            from app.services.snapshot_backfill import backfill_snapshots_for_user
            import threading
            threading.Thread(
                target=_run_snapshot_backfill_for_user,
                args=(user_id, item_id),
                daemon=True,
            ).start()
        except Exception:
            pass
        return False

    if not item.needs_backfill:
        item.needs_backfill = True
        item.backfill_attempts = 0
        item.backfill_queued_at = datetime.utcnow()
        db.commit()
        logger.info(f"Queued backfill for item {item_id} ({item.market_hash_name})")

    return True


def run_backfill_queue(db: Session) -> dict:
    """
    Process the backfill queue. Called every 2 minutes by the scheduler.
    Works through queued items one at a time until the queue is empty
    or we've been running for too long.

    Returns stats dict.
    """
    from app.services.steam_price_client import (
        process_item, make_session, fetch_item_price_history,
        build_candles, upsert_candles, update_current_price
    )

    stats = {"processed": 0, "succeeded": 0, "rate_limited": 0, "failed": 0, "skipped": 0}

    # Fetch the queue ordered by queued_at (FIFO)
    queued = db.query(Item).filter(
        Item.needs_backfill == True,
        Item.backfill_attempts < MAX_ATTEMPTS,
    ).order_by(Item.backfill_queued_at.asc()).all()

    if not queued:
        return stats

    logger.info(f"Backfill queue: {len(queued)} item(s) pending")
    session = make_session()
    now = datetime.utcnow()

    for item in queued:
        stats["processed"] += 1
        item.backfill_attempts += 1
        db.commit()

        logger.info(
            f"Backfilling {item.market_hash_name} "
            f"(attempt {item.backfill_attempts}/{MAX_ATTEMPTS})"
        )

        try:
            raw_data = fetch_item_price_history(item.market_hash_name, session)

            if raw_data is None:
                # Rate limited — fetch_item_price_history already slept 60s
                # Sleep a bit more and stop processing for this cycle
                logger.warning(f"Rate limited on {item.market_hash_name}, pausing queue")
                stats["rate_limited"] += 1
                time.sleep(RATE_LIMIT_BACKOFF)
                # Don't mark done — leave in queue for next cycle
                break

            if not raw_data:
                # Item genuinely has no Steam history (delisted, too new, etc.)
                # Don't retry forever — clear the flag
                logger.info(f"No Steam history for {item.market_hash_name} — removing from queue")
                item.needs_backfill = False
                item.last_synced_at = now
                db.commit()
                stats["skipped"] += 1
                time.sleep(DELAY_BETWEEN_ITEMS)
                continue

            # Got data — build and store candles
            candles = build_candles(raw_data, now)
            upsert_candles(db, item.id, "steam", candles)

            # Update current price
            latest_dt, latest_price, latest_volume = raw_data[-1]
            update_current_price(db, item.id, "steam", latest_price, latest_volume)

            # Mark done
            item.needs_backfill = False
            item.last_synced_at = now
            db.commit()

            total_candles = sum(len(v) for v in candles.values())
            logger.info(
                f"Backfilled {item.market_hash_name}: "
                f"{total_candles} candles written"
            )
            stats["succeeded"] += 1

            # Trigger snapshot backfill for all users who have this item
            try:
                from app.services.snapshot_backfill import backfill_snapshots_for_user, get_affected_user_ids
                user_ids = get_affected_user_ids(db, item.id)
                for uid in user_ids:
                    result = backfill_snapshots_for_user(db, uid)
                    logger.info(f"Snapshot backfill for user {uid}: {result}")
            except Exception as e:
                logger.error(f"Snapshot backfill failed for item {item.id}: {e}")

            time.sleep(DELAY_BETWEEN_ITEMS)

        except Exception as e:
            logger.error(f"Backfill error for {item.market_hash_name}: {e}")
            stats["failed"] += 1
            db.rollback()

            # If we've hit max attempts, give up
            if item.backfill_attempts >= MAX_ATTEMPTS:
                logger.error(
                    f"Giving up on {item.market_hash_name} after {MAX_ATTEMPTS} attempts"
                )
                item.needs_backfill = False
                db.commit()

            time.sleep(DELAY_BETWEEN_ITEMS)

    session.close()
    logger.info(f"Backfill queue run complete: {stats}")
    return stats


def get_queue_status(db: Session) -> dict:
    """How many items are pending backfill. Used by the API status endpoint."""
    pending = db.query(Item).filter(Item.needs_backfill == True).count()
    return {"pending": pending}
