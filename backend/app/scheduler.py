"""
APScheduler job definitions for CS2 Investment Tracker.

Schedule overview:
    Every 30 min  — CSFloat price update (bulk price-list endpoint)
    Daily  3am    — Buff163 full goods crawl (~350 pages, CNY prices)
    Daily  4am    — ByMykel item sync (SHA check, fast if no changes)
    Weekly Mon 2am — Steam Market item discovery (catches new items)
    Hourly         — Steam price history update (new candles for all items)
    Daily  1am    — Portfolio snapshots (one per user per day)

Backfill jobs (run manually, not on schedule):
    run_backfill() in steam_price_client.py — run once to seed history
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.db.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


# ---------------------------------------------------------------------------
# Job functions
# ---------------------------------------------------------------------------

def job_steam_health_check():
    """Daily Steam cookie health check — fires Telegram alert if expired."""
    logger.info("JOB: Steam health check starting")
    try:
        from app.services.health import run_scheduled_health_check
        result = run_scheduled_health_check()
        logger.info(f"JOB: Steam health check complete: {result['status']}")
    except Exception as e:
        logger.error(f"JOB: Steam health check failed: {e}")


def job_backfill_queue():
    """
    Process the backfill queue every 2 minutes.
    Works through items needing Steam price history, one at a time,
    with proper rate limit handling and retry logic.
    """
    logger.info("JOB: Backfill queue starting")
    db = SessionLocal()
    try:
        from app.services.backfill_queue import run_backfill_queue
        result = run_backfill_queue(db)
        if result["processed"] > 0:
            logger.info(f"JOB: Backfill queue complete: {result}")
    except Exception as e:
        logger.error(f"JOB: Backfill queue failed: {e}")
    finally:
        db.close()


def job_update_csfloat_prices():
    """Update CSFloat prices for all items (every 30 minutes)."""
    logger.info("JOB: CSFloat price update starting")
    db = SessionLocal()
    try:
        from app.services.price_updater import PriceUpdater
        updater = PriceUpdater(db)
        updater.update_csfloat_prices()
        logger.info("JOB: CSFloat price update complete")
    except Exception as e:
        logger.error(f"JOB: CSFloat price update failed: {e}")
    finally:
        db.close()


def job_update_buff_prices():
    """Full Buff163 goods crawl — updates CNY prices for all items (daily)."""
    logger.info("JOB: Buff163 price update starting")
    db = SessionLocal()
    try:
        from app.services.buff_client import run_buff_price_update
        result = run_buff_price_update(db)
        logger.info(f"JOB: Buff163 price update complete: {result}")
    except Exception as e:
        logger.error(f"JOB: Buff163 price update failed: {e}")
    finally:
        db.close()


def job_update_steam_history():
    """
    Hourly Steam price history update.
    Fetches latest candles for all active items.
    """
    logger.info("JOB: Steam price history update starting")
    db = SessionLocal()
    try:
        from app.services.steam_price_client import run_hourly_update
        result = run_hourly_update(db)
        logger.info(f"JOB: Steam price history update complete: {result}")
    except Exception as e:
        logger.error(f"JOB: Steam price history update failed: {e}")
    finally:
        db.close()


def job_item_sync_bymykel():
    """
    Daily ByMykel item sync.
    SHA check is fast — only does full sync if repo has changed.
    """
    logger.info("JOB: ByMykel item sync starting")
    db = SessionLocal()
    try:
        from app.services.item_sync import run_sync
        result = run_sync(db)
        logger.info(f"JOB: ByMykel item sync complete: {result}")
    except Exception as e:
        logger.error(f"JOB: ByMykel item sync failed: {e}")
    finally:
        db.close()


def job_item_sync_steam_market():
    """
    Weekly Steam Market item discovery.
    Catches new items that ByMykel hasn't added yet.
    """
    logger.info("JOB: Steam Market item sync starting")
    db = SessionLocal()
    try:
        from app.services.steam_market_sync import run_steam_market_sync
        result = run_steam_market_sync(db)
        logger.info(f"JOB: Steam Market item sync complete: {result}")
    except Exception as e:
        logger.error(f"JOB: Steam Market item sync failed: {e}")
    finally:
        db.close()

def job_portfolio_snapshots():
    """Daily portfolio snapshots."""
    logger.info("JOB: Portfolio snapshots starting")
    db = SessionLocal()
    try:
        from app.services.portfolio_snapshot import run_daily_snapshots
        result = run_daily_snapshots(db)
        logger.info(f"JOB: Portfolio snapshots complete: {result}")
    except Exception as e:
        logger.error(f"JOB: Portfolio snapshots failed: {e}")
    finally:
        db.close()

def job_update_exchange_rates():
    """Fetch daily exchange rates from Frankfurter API (daily 6am UTC)."""
    logger.info("JOB: Exchange rate update starting")
    db = SessionLocal()
    try:
        from app.services.exchange_rate_service import run_exchange_rate_update
        result = run_exchange_rate_update(db)
        logger.info(f"JOB: Exchange rate update complete: {result}")
    except Exception as e:
        logger.error(f"JOB: Exchange rate update failed: {e}")
    finally:
        db.close()
    """
    Daily portfolio snapshots.
    One row per user per day in portfolio_snapshots table.
    Powers the portfolio value over time chart.
    """
    logger.info("JOB: Portfolio snapshots starting")
    db = SessionLocal()
    try:
        from app.services.portfolio_snapshot import run_daily_snapshots
        result = run_daily_snapshots(db)
        logger.info(f"JOB: Portfolio snapshots complete: {result}")
    except Exception as e:
        logger.error(f"JOB: Portfolio snapshots failed: {e}")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Scheduler setup
# ---------------------------------------------------------------------------

def start_scheduler():
    """Initialise and start all scheduled jobs."""

    # Steam health check — every 30 minutes
    scheduler.add_job(
        job_steam_health_check,
        "interval",
        minutes=30,
        id="steam_health_check",
        replace_existing=True,
    )

    # Backfill queue — every 2 minutes
    scheduler.add_job(
        job_backfill_queue,
        "interval",
        minutes=2,
        id="backfill_queue",
        replace_existing=True,
    )

    # CSFloat — every 30 minutes
    scheduler.add_job(
        job_update_csfloat_prices,
        "interval",
        minutes=30,
        id="update_csfloat_prices",
        replace_existing=True,
    )

    # Buff163 — daily at 3am UTC
    scheduler.add_job(
        job_update_buff_prices,
        CronTrigger(hour=3, minute=0),
        id="update_buff_prices",
        replace_existing=True,
    )

    # Steam price history — every hour
    scheduler.add_job(
        job_update_steam_history,
        "interval",
        hours=1,
        id="update_steam_history",
        replace_existing=True,
    )

    # ByMykel item sync — daily at 4am UTC
    scheduler.add_job(
        job_item_sync_bymykel,
        CronTrigger(hour=4, minute=0),
        id="item_sync_bymykel",
        replace_existing=True,
    )

    # Steam Market item discovery — weekly Monday 2am UTC
    scheduler.add_job(
        job_item_sync_steam_market,
        CronTrigger(day_of_week="mon", hour=2, minute=0),
        id="item_sync_steam_market",
        replace_existing=True,
    )

    # Exchange rates — daily at 6am UTC (after ECB publishes)
    scheduler.add_job(
        job_update_exchange_rates,
        CronTrigger(hour=6, minute=0),
        id="update_exchange_rates",
        replace_existing=True,
    )

    # Portfolio snapshots — daily at 1am UTC
    scheduler.add_job(
        job_portfolio_snapshots,
        CronTrigger(hour=1, minute=0),
        id="portfolio_snapshots",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler started with jobs: "
        "CSFloat(30min), Buff(daily 3am), Steam history(hourly), "
        "ByMykel sync(daily 4am), Steam Market sync(weekly Mon 2am), "
        "Exchange rates(daily 6am), Portfolio snapshots(daily 1am)"
    )


def stop_scheduler():
    """Stop the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
