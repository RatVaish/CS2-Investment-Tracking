"""
Currency conversion utility.

Converts prices from their native currency to USD.
Uses exchange_rates table if populated, falls back to hardcoded rates.

Native currencies per market:
    csfloat → USD (no conversion needed)
    steam   → GBP (UK Steam accounts) → needs GBP→USD
    buff163 → CNY → needs CNY→USD
"""

import logging
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Fallback rates if exchange_rates table is empty
# Updated periodically — these are approximate
FALLBACK_RATES_TO_USD = {
    "USD": 1.0,
    "GBP": 1.27,   # 1 GBP = 1.27 USD
    "EUR": 1.09,
    "CNY": 0.138,  # 1 CNY = 0.138 USD
    "AUD": 0.64,
    "CAD": 0.74,
}

_rate_cache = {}


def get_rate_to_usd(from_currency: str, db: Optional[Session] = None) -> float:
    """
    Get conversion rate from a currency to USD.
    Tries DB first, falls back to hardcoded rates.
    """
    if from_currency == "USD":
        return 1.0

    # Check cache (valid for current process lifetime)
    if from_currency in _rate_cache:
        return _rate_cache[from_currency]

    # Try DB
    if db:
        try:
            from app.models.exchange_rate import ExchangeRate
            rate_row = db.query(ExchangeRate).filter(
                ExchangeRate.from_currency == from_currency,
                ExchangeRate.to_currency == "USD",
            ).order_by(ExchangeRate.date.desc()).first()

            if rate_row:
                _rate_cache[from_currency] = rate_row.rate
                return rate_row.rate
        except Exception as e:
            logger.warning(f"Failed to fetch exchange rate from DB: {e}")

    # Use fallback
    rate = FALLBACK_RATES_TO_USD.get(from_currency, 1.0)
    if from_currency not in FALLBACK_RATES_TO_USD:
        logger.warning(f"No exchange rate for {from_currency}, defaulting to 1.0")
    return rate


def to_usd(amount: Optional[float], from_currency: str, db: Optional[Session] = None) -> Optional[float]:
    """Convert an amount from any currency to USD."""
    if amount is None:
        return None
    rate = get_rate_to_usd(from_currency, db)
    return round(amount * rate, 4)


def seed_exchange_rates(db: Session):
    """
    Seed today's exchange rates using fallback values.
    Call this once to populate the exchange_rates table.
    """
    from app.models.exchange_rate import ExchangeRate
    today = date.today()

    pairs = [
        ("GBP", "USD", FALLBACK_RATES_TO_USD["GBP"]),
        ("CNY", "USD", FALLBACK_RATES_TO_USD["CNY"]),
        ("EUR", "USD", FALLBACK_RATES_TO_USD["EUR"]),
        ("AUD", "USD", FALLBACK_RATES_TO_USD["AUD"]),
        ("CAD", "USD", FALLBACK_RATES_TO_USD["CAD"]),
    ]

    for from_c, to_c, rate in pairs:
        existing = db.query(ExchangeRate).filter(
            ExchangeRate.from_currency == from_c,
            ExchangeRate.to_currency == to_c,
            ExchangeRate.date == today,
        ).first()

        if not existing:
            db.add(ExchangeRate(
                from_currency=from_c,
                to_currency=to_c,
                rate=rate,
                source="fallback",
                date=today,
            ))

    db.commit()
    logger.info("Exchange rates seeded")
