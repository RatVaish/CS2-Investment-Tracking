"""
Exchange Rate Service

Fetches daily FX rates from Frankfurter API (https://api.frankfurter.app).
Free, no API key required, maintained by the European Central Bank data.

Runs daily at 6am UTC (after ECB publishes rates at ~4pm CET previous day).

Currencies we track (all relative to USD):
    GBP - British Pound (Steam UK prices)
    CNY - Chinese Yuan (Buff163 prices)
    EUR - Euro
    AUD - Australian Dollar
    CAD - Canadian Dollar
"""

import requests
import logging
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.exchange_rate import ExchangeRate
from app.models.price_update_log import PriceUpdateLog

logger = logging.getLogger(__name__)

FRANKFURTER_URL = "https://api.frankfurter.app/latest"
TARGET_CURRENCIES = ["GBP", "CNY", "EUR", "AUD", "CAD"]


def fetch_rates_from_frankfurter() -> Optional[dict]:
    """
    Fetch latest rates from Frankfurter API.
    Base currency: USD. Returns dict of {currency: rate_to_usd}.

    Frankfurter returns rates FROM base TO targets, so:
        base=EUR, amount=1 EUR = X USD
    We want: 1 GBP = X USD etc.
    So we use USD as base and invert: 1/rate = currency_to_usd
    Actually easier: use each currency as base, get USD rate directly.
    """
    try:
        # Get rates with USD as the target
        # ?from=GBP&to=USD gives us: 1 GBP = X USD
        # Fetch all in one call by using USD as base and inverting
        response = requests.get(
            FRANKFURTER_URL,
            params={
                "from": "USD",
                "to": ",".join(TARGET_CURRENCIES),
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        # data["rates"] = {"GBP": 0.79, "CNY": 7.24, ...}
        # These are: 1 USD = X foreign currency
        # We want: 1 foreign currency = X USD → invert
        rates_to_usd = {}
        for currency, rate_per_usd in data["rates"].items():
            if rate_per_usd > 0:
                rates_to_usd[currency] = round(1 / rate_per_usd, 6)

        logger.info(f"Fetched exchange rates: {rates_to_usd}")
        return rates_to_usd

    except requests.exceptions.Timeout:
        logger.error("Timeout fetching exchange rates from Frankfurter")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch exchange rates: {e}")
        return None


def store_rates(db: Session, rates: dict, today: date) -> int:
    """
    Upsert exchange rates into DB.
    Returns number of rates stored.
    """
    stored = 0
    for currency, rate in rates.items():
        existing = db.query(ExchangeRate).filter(
            ExchangeRate.from_currency == currency,
            ExchangeRate.to_currency == "USD",
            ExchangeRate.date == today,
        ).first()

        if existing:
            existing.rate = rate
            existing.source = "frankfurter"
        else:
            db.add(ExchangeRate(
                from_currency=currency,
                to_currency="USD",
                rate=rate,
                source="frankfurter",
                date=today,
            ))
        stored += 1

    db.commit()
    return stored


def seed_fallback_rates(db: Session):
    """
    Seed today's rates with hardcoded fallbacks.
    Used when Frankfurter is unavailable.
    """
    FALLBACK = {
        "GBP": 1.27,
        "CNY": 0.138,
        "EUR": 1.09,
        "AUD": 0.64,
        "CAD": 0.74,
    }
    today = date.today()
    stored = store_rates(db, FALLBACK, today)
    logger.info(f"Seeded {stored} fallback exchange rates")
    return stored


def run_exchange_rate_update(db: Session) -> dict:
    """
    Main entry point — fetch and store today's exchange rates.
    Called daily by scheduler at 6am UTC.
    Falls back to hardcoded rates if API unavailable.
    """
    logger.info("Starting exchange rate update...")
    start_time = datetime.utcnow()
    today = date.today()

    # Check if we already have today's rates
    existing = db.query(ExchangeRate).filter(
        ExchangeRate.date == today,
        ExchangeRate.to_currency == "USD",
    ).count()

    if existing >= len(TARGET_CURRENCIES):
        logger.info(f"Exchange rates already up to date for {today}")
        return {"status": "already_current", "date": str(today)}

    # Try Frankfurter first
    rates = fetch_rates_from_frankfurter()

    if rates:
        stored = store_rates(db, rates, today)
        logger.info(f"Stored {stored} exchange rates from Frankfurter for {today}")
        return {"status": "success", "rates": rates, "date": str(today)}
    else:
        # Fall back to hardcoded rates
        logger.warning("Frankfurter unavailable, using fallback rates")
        stored = seed_fallback_rates(db)
        return {"status": "fallback", "stored": stored, "date": str(today)}
