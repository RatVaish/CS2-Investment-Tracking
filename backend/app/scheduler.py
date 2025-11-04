from apscheduler.schedulers.background import BackgroundScheduler
from app.services.price_service import update_all_prices
from app.db.session import SessionLocal
from datetime import datetime

def scheduled_price_update():
    """
    Run automatic price updates for all investments
    in the background for all investments.
    """

    print(f"\n{'=' * 60}")
    print(f"🔄 Starting scheduled price update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    db = SessionLocal()
    try:
        result = update_all_prices(db)
        print(f"\n{'=' * 60}")
        print(f"✅ Scheduled update complete!")
        print(f"   Total: {result['total']} items")
        print(f"   Updated: {result['updated']} items")
        print(f"   Failed: {result['failed']} items")
        print(f"   Rate Limited: {result['rate_limited']} items")
        print(f"   Next update in 1 hour")
        print(f"{'=' * 60}\n")
    except Exception as e:
        print(f"\n{'=' * 60}")
        print(f"❌ Scheduled update failed: {str(e)}")
        print(f"{'=' * 60}\n")
    finally:
        db.close()


def start_scheduler():
    """
    Initialize and start the background scheduler
    Runs price updates every hour
    """
    scheduler = BackgroundScheduler()

    # Schedule price updates every hour
    # You can adjust the interval by changing 'hours=1'
    scheduler.add_job(
        scheduled_price_update,
        'interval',
        hours=1,  # Run every hour
        id='price_update_job',
        name='Update all investment prices',
        replace_existing=True
    )

    scheduler.start()
    print("\n" + "=" * 60)
    print("📅 Price Update Scheduler Started!")
    print("   Frequency: Every 1 hour")
    print("   Status: Active")
    print("   Note: Prices will update automatically while backend is running")
    print("=" * 60 + "\n")

    return scheduler
