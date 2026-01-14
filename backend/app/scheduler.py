from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.price_updater import PriceUpdater
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def update_csfloat_prices():
    """Update CSFloat prices for ALL items (runs every 30 minutes)"""
    logger.info("Starting CSFloat price update job")
    db = SessionLocal()
    try:
        updater = PriceUpdater(db)
        updater.update_csfloat_prices()
        logger.info("CSFloat price update completed")
    except Exception as e:
        logger.error(f"CSFloat price update failed: {e}")
    finally:
        db.close()


def update_buff_prices():
    """Update Buff prices for ALL items (runs every 30 minutes)"""
    logger.info("Starting Buff price update job")
    db = SessionLocal()
    try:
        updater = PriceUpdater(db)
        updater.update_buff_prices()
        logger.info("Buff price update completed")
    except Exception as e:
        logger.error(f"Buff price update failed: {e}")
    finally:
        db.close()


def update_steam_prices():
    """Update Steam prices for ALL items (runs weekly)"""
    logger.info("Starting Steam price update job")
    db = SessionLocal()
    try:
        updater = PriceUpdater(db)
        updater.update_steam_prices()
        logger.info("Steam price update completed")
    except Exception as e:
        logger.error(f"Steam price update failed: {e}")
    finally:
        db.close()


def compress_old_hourly_data():
    """Compress hourly data older than 30 days into daily candles (runs daily at midnight)"""
    logger.info("Starting hourly data compression")
    db = SessionLocal()
    try:
        updater = PriceUpdater(db)
        updater.compress_old_hourly_data()
        logger.info("Hourly data compression completed")
    except Exception as e:
        logger.error(f"Hourly data compression failed: {e}")
    finally:
        db.close()


def start_scheduler():
    """Initialize and start all scheduled jobs"""

    # CSFloat prices - every 30 minutes
    scheduler.add_job(
        update_csfloat_prices,
        'interval',
        minutes=30,
        id='update_csfloat_prices',
        replace_existing=True
    )

    # Buff prices - every 30 minutes (offset by 15 min from CSFloat)
    scheduler.add_job(
        update_buff_prices,
        'interval',
        minutes=30,
        id='update_buff_prices',
        replace_existing=True,
        next_run_time=None  # Start immediately, then every 30 min
    )

    # Steam prices - weekly on Monday at 3 AM UTC
    scheduler.add_job(
        update_steam_prices,
        CronTrigger(day_of_week='mon', hour=3, minute=0),
        id='update_steam_prices',
        replace_existing=True
    )

    # Compress old hourly data - daily at midnight UTC
    scheduler.add_job(
        compress_old_hourly_data,
        CronTrigger(hour=0, minute=0),
        id='compress_old_hourly_data',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started with all jobs")


def stop_scheduler():
    """Stop the scheduler gracefully"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
        