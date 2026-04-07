from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.price_history import PriceHistory
from app.models.item import Item
from app.models.item_price import ItemPrice
from app.crud import investment as crud_investment

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

    # On-demand backfill for Steam on first view
    existing_count = db.query(PriceHistory).filter(
        PriceHistory.item_id == item_id,
        PriceHistory.market == market,
    ).count()

    if existing_count == 0 and market == "steam":
        try:
            from app.services.steam_price_client import process_item, make_session
            session = make_session()
            now = datetime.utcnow()
            process_item(db, item, session, now)
            session.close()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"On-demand backfill failed for {item.market_hash_name}: {e}")

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
