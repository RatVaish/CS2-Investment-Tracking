from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import csv
import io
import logging

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.price_history import PriceHistory
from app.models.item import Item
from app.models.item_price import ItemPrice
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.crud import investment as crud_investment

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary")
def get_portfolio_summary(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Portfolio summary totals."""
    return crud_investment.get_portfolio_summary(db, user_id=current_user.id)


@router.get("/top-performers")
def get_top_performers(
        limit: int = 5,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Top and worst performing investments by ROI."""
    investments = crud_investment.get_investments_with_items(
        db, user_id=current_user.id, limit=10000, status="active"
    )
    priced = [inv for inv in investments if inv["current_price"] is not None]
    top = sorted(priced, key=lambda x: x["roi"] or 0, reverse=True)[:limit]
    worst = sorted(priced, key=lambda x: x["roi"] or 0)[:limit]
    return {"top_performers": top, "worst_performers": worst}


@router.get("/price-history/{item_id}")
def get_item_price_history(
        item_id: int,
        market: str = Query("steam", description="steam | csfloat | buff163"),
        resolution: str = Query("daily", description="hourly | daily | weekly"),
        days: Optional[int] = Query(None, description="Days of history (default: all)"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    OHLV candlestick price history for an item.

    On first request for a Steam item with no history:
    triggers an on-demand backfill from Steam price history API.

    For daily/weekly resolution: automatically fills the recent gap
    by including hourly data from the last 30 days, downsampled to
    one point per day (using the last hourly close of each day).
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # On first view: queue the item for async backfill instead of blocking the request
    existing_count = db.query(PriceHistory).filter(
        PriceHistory.item_id == item_id,
        PriceHistory.market == market,
    ).count()

    if existing_count == 0 and market == "steam":
        try:
            from app.services.backfill_queue import queue_item_for_backfill
            queued = queue_item_for_backfill(db, item_id)
            if queued:
                logger.info(f"Queued item {item_id} for backfill")
        except Exception as e:
            logger.error(f"Failed to queue backfill for item {item_id}: {e}")

    # Fetch requested resolution candles
    query = db.query(PriceHistory).filter(
        PriceHistory.item_id == item_id,
        PriceHistory.market == market,
        PriceHistory.resolution == resolution,
    )
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(PriceHistory.candle_timestamp >= cutoff)

    candles = query.order_by(PriceHistory.candle_timestamp.asc()).all()

    # For daily/weekly: fill the recent gap with hourly data
    # The last 30 days are stored as hourly, not daily
    if resolution in ('daily', 'weekly'):
        from collections import defaultdict

        # Find the most recent daily candle timestamp
        most_recent_daily = candles[-1].candle_timestamp if candles else None
        gap_start = most_recent_daily if most_recent_daily else (
            datetime.utcnow() - timedelta(days=days or 9999)
        )

        # Fetch hourly candles newer than our most recent daily
        hourly_candles = db.query(PriceHistory).filter(
            PriceHistory.item_id == item_id,
            PriceHistory.market == market,
            PriceHistory.resolution == 'hourly',
            PriceHistory.candle_timestamp > gap_start,
        ).order_by(PriceHistory.candle_timestamp.asc()).all()

        if hourly_candles:
            # Downsample hourly → daily: group by date, take last close of each day
            daily_groups = defaultdict(list)
            for hc in hourly_candles:
                day_key = hc.candle_timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
                daily_groups[day_key].append(hc)

            # Build synthetic daily candles from hourly groups
            synthetic = []
            for day_ts in sorted(daily_groups.keys()):
                hours = daily_groups[day_ts]
                synthetic.append({
                    "timestamp": day_ts.isoformat(),
                    "open": hours[0].open_price,
                    "high": max(h.high_price for h in hours if h.high_price),
                    "low": min(h.low_price for h in hours if h.low_price),
                    "close": hours[-1].close_price,
                    "volume": sum(h.volume or 0 for h in hours),
                })

            # Build response from stored candles + synthetic recent days
            stored = [
                {
                    "timestamp": c.candle_timestamp.isoformat(),
                    "open": c.open_price,
                    "high": c.high_price,
                    "low": c.low_price,
                    "close": c.close_price,
                    "volume": c.volume,
                }
                for c in candles
            ]

            return {
                "item_id": item_id,
                "market_hash_name": item.market_hash_name,
                "market": market,
                "resolution": resolution,
                "currency": candles[0].currency if candles else "USD",
                "backfilled": existing_count == 0,
                "candles": stored + synthetic,
                "count": len(stored) + len(synthetic),
            }

    return {
        "item_id": item_id,
        "market_hash_name": item.market_hash_name,
        "market": market,
        "resolution": resolution,
        "currency": candles[0].currency if candles else "USD",
        "backfilled": existing_count == 0,
        "queued_for_backfill": item.needs_backfill if existing_count == 0 else False,
        "candles": [
            {
                "timestamp": c.candle_timestamp.isoformat(),
                "open": c.open_price,
                "high": c.high_price,
                "low": c.low_price,
                "close": c.close_price,
                "volume": c.volume,
            }
            for c in candles
        ],
        "count": len(candles),
    }


@router.get("/backfill-status/{item_id}")
def get_backfill_status(
        item_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Poll whether an item's backfill is complete. Frontend uses this to know when to refresh."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    candle_count = db.query(PriceHistory).filter(
        PriceHistory.item_id == item_id,
        PriceHistory.market == "steam",
    ).count()

    return {
        "item_id": item_id,
        "needs_backfill": item.needs_backfill,
        "backfill_attempts": item.backfill_attempts,
        "has_data": candle_count > 0,
        "candle_count": candle_count,
    }


@router.get("/available-markets/{item_id}")
def get_available_markets(
        item_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Which markets have price data for this item. Used to show/hide chart tabs."""
    prices = db.query(ItemPrice).filter(ItemPrice.item_id == item_id).all()
    return {
        "item_id": item_id,
        "markets": [
            {
                "market": p.market,
                "price": p.price,
                "currency": p.currency,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in prices
        ]
    }


@router.get("/snapshots")
def get_portfolio_snapshots(
        days: Optional[int] = Query(90, description="Days of history"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Portfolio value over time from daily snapshots.
    Powers the dashboard chart with real data.
    """
    cutoff = datetime.utcnow() - timedelta(days=days or 9999)
    snapshots = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == current_user.id,
        PortfolioSnapshot.snapshot_date >= cutoff.date(),
    ).order_by(PortfolioSnapshot.snapshot_date.asc()).all()

    return {
        "days": days,
        "count": len(snapshots),
        "snapshots": [
            {
                "date": s.snapshot_date.isoformat(),
                "total_invested": s.total_invested,
                "total_current_value": s.total_current_value,
                "total_profit_loss": s.total_profit_loss,
                "overall_roi": s.overall_roi,
                "open_positions": s.open_positions,
            }
            for s in snapshots
        ],
    }


@router.post("/snapshots/trigger")
def trigger_snapshot(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Manually trigger a snapshot for the current user (useful after first login)."""
    from app.services.portfolio_snapshot import take_snapshot_for_user
    result = take_snapshot_for_user(db, current_user)
    return result


@router.get("/export/csv")
def export_investments_csv(
        status: Optional[str] = Query(None, description="active | sold | all"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Export all investments as CSV. Pro feature.
    """
    if current_user.tier != "pro":
        raise HTTPException(status_code=403, detail="CSV export is a Pro feature. Upgrade to download your data.")

    fetch_status = None if status == "all" else (status or "active")
    investments = crud_investment.get_investments_with_items(
        db, user_id=current_user.id, limit=100000, status=fetch_status
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Item", "Type", "Rarity", "Wear", "StatTrak",
        "Quantity", "Purchase Price (USD)", "Total Invested (USD)",
        "Steam Price (USD)", "CSFloat Price (USD)", "Buff163 Price (USD)",
        "Current Value (USD)", "P&L (USD)", "ROI (%)",
        "Status", "Purchase Date", "Sold Price (USD)", "Sold Date",
        "Float Value", "Notes",
    ])

    for inv in investments:
        item = inv.get("item", {})
        prices = inv.get("prices", {})
        steam_price = (prices.get("steam") or {}).get("price")
        csfloat_price = (prices.get("csfloat") or {}).get("price")
        buff_price = (prices.get("buff163") or {}).get("price")

        purchase_date = ""
        if inv.get("purchase_date"):
            try:
                purchase_date = inv["purchase_date"].strftime("%Y-%m-%d")
            except Exception:
                purchase_date = str(inv["purchase_date"])[:10]

        sold_date = ""
        if inv.get("sold_at"):
            try:
                sold_date = inv["sold_at"].strftime("%Y-%m-%d")
            except Exception:
                sold_date = str(inv["sold_at"])[:10]

        writer.writerow([
            inv["id"],
            item.get("market_hash_name", ""),
            item.get("item_type", ""),
            item.get("rarity", ""),
            item.get("wear", ""),
            "Yes" if item.get("is_stattrak") else "No",
            inv["quantity"],
            inv["purchase_price"],
            inv["total_invested"],
            round(steam_price, 4) if steam_price else "",
            round(csfloat_price, 4) if csfloat_price else "",
            round(buff_price, 4) if buff_price else "",
            inv.get("current_value") or "",
            inv.get("profit_loss") or "",
            inv.get("roi") or "",
            inv["status"],
            purchase_date,
            inv.get("sold_price") or "",
            sold_date,
            inv.get("wear_value") or "",
            inv.get("notes") or "",
        ])

    output.seek(0)
    filename = f"floatbase_portfolio_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/performance")
def get_portfolio_performance(
        days: Optional[int] = Query(None, description="Window in days. None = all time (vs purchase cost)"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Rolling performance for a time window.

    days=30  → P&L vs portfolio value 30 days ago (from snapshots)
    days=None → P&L vs actual purchase cost (all-time)

    Returns start_value, current_value, period_pnl, period_roi
    plus the snapshot series for the chart.
    """
    from app.crud.investment import get_portfolio_summary

    summary = get_portfolio_summary(db, user_id=current_user.id)
    current_value = summary["total_current_value"]
    total_invested = summary["total_invested"]

    # Gap check — if user has investments but missing snapshots, backfill in background
    if summary["total_investments"] > 0:
        try:
            from app.models.portfolio_snapshot import PortfolioSnapshot
            from app.models.investment import Investment as InvModel
            import threading

            snapshot_count = db.query(PortfolioSnapshot).filter(
                PortfolioSnapshot.user_id == current_user.id
            ).count()

            # Find earliest purchase date
            earliest = db.query(InvModel.purchase_date).filter(
                InvModel.user_id == current_user.id,
                InvModel.purchase_date.isnot(None),
            ).order_by(InvModel.purchase_date.asc()).first()

            if earliest and earliest[0]:
                from datetime import date, timedelta
                days_since_earliest = (date.today() - earliest[0].date()).days
                # If we have fewer snapshots than days since earliest purchase, backfill
                if snapshot_count < days_since_earliest - 1:
                    def _bg_backfill(uid):
                        from app.db.session import SessionLocal
                        from app.services.snapshot_backfill import backfill_snapshots_for_user
                        _db = SessionLocal()
                        try:
                            backfill_snapshots_for_user(_db, uid)
                        except Exception as e:
                            logger.error(f"Background snapshot backfill failed: {e}")
                        finally:
                            _db.close()
                    threading.Thread(target=_bg_backfill, args=(current_user.id,), daemon=True).start()
        except Exception as e:
            logger.warning(f"Gap check failed (non-critical): {e}")

    if days is None:
        # ALL TIME — compare against actual purchase cost
        period_pnl = summary["total_profit_loss"]
        period_roi = summary["overall_roi"]
        start_value = total_invested
        start_date = None
        snapshot_series = []

        # Still return full snapshot series for the chart
        all_snapshots = db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.user_id == current_user.id,
        ).order_by(PortfolioSnapshot.snapshot_date.asc()).all()

        snapshot_series = [
            {
                "date": s.snapshot_date.isoformat(),
                "value": s.total_current_value,
                "total_profit_loss": s.total_profit_loss,
            }
            for s in all_snapshots
        ]

    else:
        # WINDOWED — find snapshot closest to N days ago
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Get the snapshot nearest to but not after the cutoff
        start_snapshot = db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.user_id == current_user.id,
            PortfolioSnapshot.snapshot_date <= cutoff.date(),
        ).order_by(PortfolioSnapshot.snapshot_date.desc()).first()

        # Get snapshots within the window for the chart
        window_snapshots = db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.user_id == current_user.id,
            PortfolioSnapshot.snapshot_date >= cutoff.date(),
        ).order_by(PortfolioSnapshot.snapshot_date.asc()).all()

        snapshot_series = [
            {
                "date": s.snapshot_date.isoformat(),
                "value": s.total_current_value,
                "total_profit_loss": s.total_profit_loss,
            }
            for s in window_snapshots
        ]

        if start_snapshot:
            start_value = start_snapshot.total_current_value
            start_date = start_snapshot.snapshot_date.isoformat()
        else:
            # No snapshot that old — fall back to purchase cost as anchor
            start_value = total_invested
            start_date = None

        if start_value and start_value > 0:
            period_pnl = round(current_value - start_value, 2)
            period_roi = round((period_pnl / start_value) * 100, 2)
        else:
            period_pnl = 0.0
            period_roi = 0.0

    return {
        "days": days,
        "start_value": round(start_value, 2) if start_value else None,
        "start_date": start_date if days else None,
        "current_value": round(current_value, 2),
        "total_invested": round(total_invested, 2),
        "period_pnl": period_pnl,
        "period_roi": period_roi,
        "has_snapshot_data": len(snapshot_series) > 0,
        "snapshots": snapshot_series,
    }


@router.get("/predict-entry-date/{item_id}")
def predict_entry_date(
        item_id: int,
        month: int = Query(..., ge=1, le=12),
        year: int = Query(..., ge=2013, le=2030),
        purchase_price: float = Query(..., gt=0),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    Given an item, a month/year, and a purchase price, find the candle
    in that month whose close price is closest to the purchase price.
    Returns the predicted date and the candle's close for context.

    Resolution priority: hourly > daily > weekly (most granular available).
    Falls back gracefully if no data exists for that month.
    """
    from calendar import monthrange
    from sqlalchemy import and_

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Window: full calendar month
    month_start = datetime(year, month, 1)
    last_day = monthrange(year, month)[1]
    month_end = datetime(year, month, last_day, 23, 59, 59)

    best_candle = None
    for resolution in ('hourly', 'daily', 'weekly'):
        candles = db.query(PriceHistory).filter(
            and_(
                PriceHistory.item_id == item_id,
                PriceHistory.market == 'steam',
                PriceHistory.resolution == resolution,
                PriceHistory.candle_timestamp >= month_start,
                PriceHistory.candle_timestamp <= month_end,
            )
        ).order_by(PriceHistory.candle_timestamp.asc()).all()

        if candles:
            # Find candle whose close is nearest to purchase_price
            best_candle = min(
                candles,
                key=lambda c: abs((c.close_price or 0) - purchase_price)
            )
            break

    if not best_candle:
        # No price history for that month at all — fall back to mid-month
        mid = datetime(year, month, min(15, monthrange(year, month)[1]))
        return {
            "item_id": item_id,
            "predicted_date": mid.isoformat(),
            "predicted_date_display": mid.strftime("%-d %b %Y"),
            "candle_close": None,
            "price_delta": None,
            "confidence": "none",
            "fallback": True,
            "message": f"No price history found for {item.market_hash_name} in {month}/{year}. Using mid-month estimate.",
        }

    ts = best_candle.candle_timestamp
    delta = abs((best_candle.close_price or 0) - purchase_price)
    pct_diff = (delta / purchase_price * 100) if purchase_price > 0 else 100

    # Confidence based on how close the nearest candle price is to what they paid
    if pct_diff < 3:
        confidence = "high"
    elif pct_diff < 10:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "item_id": item_id,
        "predicted_date": ts.isoformat(),
        "predicted_date_display": ts.strftime("%-d %b %Y"),
        "candle_close": round(best_candle.close_price, 4) if best_candle.close_price else None,
        "price_delta": round(delta, 4),
        "price_delta_pct": round(pct_diff, 2),
        "confidence": confidence,   # "high" | "medium" | "low" | "none"
        "fallback": False,
        "message": None,
    }
