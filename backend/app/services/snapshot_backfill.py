"""
Snapshot Backfill Service

Triggered after Steam price history is successfully fetched for an item.
Walks back through a user's investment history and writes portfolio_snapshots
for every day from their earliest purchase date to yesterday.

Uses only price_history candles already in the DB — no external API calls.
Skips dates that already have a snapshot (never overwrites existing data).
For each date, uses the nearest available candle to that date per item.
"""

import logging
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.investment import Investment
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.price_history import PriceHistory

logger = logging.getLogger(__name__)


def _get_nearest_price(db: Session, item_id: int, target_date: date) -> float | None:
    """
    Find the closest daily/weekly candle close_price for an item on or before target_date.
    Prefers daily resolution, falls back to weekly.
    Returns None if no candle exists at all.
    """
    target_dt = datetime.combine(target_date, datetime.min.time())

    # Try daily first (covers up to 1 year of history)
    candle = db.query(PriceHistory).filter(
        PriceHistory.item_id == item_id,
        PriceHistory.market == 'steam',
        PriceHistory.resolution.in_(['daily', 'weekly']),
        PriceHistory.candle_timestamp <= target_dt,
    ).order_by(PriceHistory.candle_timestamp.desc()).first()

    return candle.close_price if candle and candle.close_price else None


def backfill_snapshots_for_user(db: Session, user_id: int) -> dict:
    """
    Backfill portfolio_snapshots for a user from their earliest purchase date to yesterday.

    Called after price history backfill completes for any of their items.
    Safe to call multiple times — skips dates that already have snapshots.
    """
    yesterday = date.today() - timedelta(days=1)

    # Get all active investments for this user
    investments = db.query(Investment).filter(
        Investment.user_id == user_id,
        Investment.status.in_(['active', 'sold']),  # include sold — they were active historically
    ).all()

    if not investments:
        return {"skipped": "no investments"}

    # Find earliest purchase date across all investments
    earliest = min(
        (inv.purchase_date.date() if inv.purchase_date else date.today())
        for inv in investments
    )

    if earliest >= yesterday:
        return {"skipped": "no historical dates to fill"}

    # Find which dates already have snapshots
    existing_dates = set(
        row.snapshot_date for row in db.query(PortfolioSnapshot.snapshot_date).filter(
            PortfolioSnapshot.user_id == user_id,
            PortfolioSnapshot.snapshot_date >= earliest,
            PortfolioSnapshot.snapshot_date <= yesterday,
        ).all()
    )

    # Walk each date from earliest to yesterday
    current_date = earliest
    created = 0
    skipped = 0

    while current_date <= yesterday:
        if current_date in existing_dates:
            current_date += timedelta(days=1)
            skipped += 1
            continue

        # Which investments were active on this date?
        active_on_date = [
            inv for inv in investments
            if (inv.purchase_date and inv.purchase_date.date() <= current_date)
            and (inv.status == 'active' or (inv.sold_at and inv.sold_at.date() > current_date))
        ]

        if not active_on_date:
            current_date += timedelta(days=1)
            continue

        # Calculate portfolio value on this date
        total_invested = sum(inv.purchase_price * inv.quantity for inv in active_on_date)
        total_value = 0.0
        priced_invested = 0.0

        for inv in active_on_date:
            price = _get_nearest_price(db, inv.item_id, current_date)
            if price:
                total_value += price * inv.quantity
                priced_invested += inv.purchase_price * inv.quantity

        # Skip dates where we have no price data at all
        if total_value == 0:
            current_date += timedelta(days=1)
            continue

        pnl = round(total_value - total_invested, 2)
        roi = round((pnl / total_invested * 100), 2) if total_invested > 0 else 0.0

        snapshot = PortfolioSnapshot(
            user_id=user_id,
            snapshot_date=current_date,
            total_invested=round(total_invested, 2),
            total_current_value=round(total_value, 2),
            total_profit_loss=pnl,
            overall_roi=roi,
            open_positions=len(active_on_date),
        )
        db.add(snapshot)
        created += 1
        current_date += timedelta(days=1)

    db.commit()
    logger.info(f"Snapshot backfill for user {user_id}: {created} created, {skipped} skipped")
    return {"created": created, "skipped": skipped, "from_date": str(earliest), "to_date": str(yesterday)}


def get_affected_user_ids(db: Session, item_id: int) -> list[int]:
    """Get all user IDs who have investments in a specific item."""
    rows = db.query(Investment.user_id).filter(
        Investment.item_id == item_id,
    ).distinct().all()
    return [row.user_id for row in rows]
