"""
Portfolio Snapshot Service

Writes one row per user per day to portfolio_snapshots.
Called nightly by the scheduler — powers the dashboard portfolio value chart.
"""

import logging
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.crud.investment import get_portfolio_summary

logger = logging.getLogger(__name__)


def take_snapshot_for_user(db: Session, user: User) -> dict:
    """Write today's portfolio snapshot for a single user."""
    today = date.today()

    # Check if snapshot already exists for today
    existing = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user.id,
        PortfolioSnapshot.snapshot_date == today,
    ).first()

    summary = get_portfolio_summary(db, user_id=user.id)

    if existing:
        # Update in place (prices change, we want end-of-day value)
        existing.total_invested = summary["total_invested"]
        existing.total_current_value = summary["total_current_value"]
        existing.total_profit_loss = summary["total_profit_loss"]
        existing.overall_roi = summary["overall_roi"]
        existing.open_positions = summary["total_investments"]
        db.commit()
        return {"action": "updated", "user_id": user.id, "date": str(today)}

    snapshot = PortfolioSnapshot(
        user_id=user.id,
        snapshot_date=today,
        total_invested=summary["total_invested"],
        total_current_value=summary["total_current_value"],
        total_profit_loss=summary["total_profit_loss"],
        overall_roi=summary["overall_roi"],
        open_positions=summary["total_investments"],
    )
    db.add(snapshot)
    db.commit()
    return {"action": "created", "user_id": user.id, "date": str(today)}


def run_daily_snapshots(db: Session) -> dict:
    """Take snapshots for all active users. Called by scheduler."""
    users = db.query(User).filter(User.is_active == True).all()
    results = {"total": len(users), "created": 0, "updated": 0, "failed": 0}

    for user in users:
        try:
            result = take_snapshot_for_user(db, user)
            results[result["action"]] += 1
        except Exception as e:
            logger.error(f"Snapshot failed for user {user.id}: {e}")
            results["failed"] += 1

    logger.info(f"Portfolio snapshots: {results}")
    return results
