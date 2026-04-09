"""
Health check service.

Tracks the status of external dependencies — currently Steam.
Results are stored in memory (process lifetime) and exposed via API.
The scheduler runs a daily check and fires Telegram alerts on state changes.
"""

import logging
import requests
from datetime import datetime
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory state — persists for the lifetime of the backend process
_steam_status = {
    "status": "unknown",          # "ok" | "expired" | "rate_limited" | "unknown"
    "last_checked": None,         # datetime
    "last_ok": None,              # datetime of last successful check
    "candle_count": None,         # number of data points returned on last ok check
}

TEST_ITEM = "AK-47 | Redline (Field-Tested)"  # Liquid item, always has history


def check_steam_health() -> dict:
    """
    Make a real test request to Steam pricehistory.
    Updates internal state and returns the result dict.
    """
    global _steam_status

    if not settings.STEAM_LOGIN_SECURE:
        _steam_status["status"] = "unconfigured"
        _steam_status["last_checked"] = datetime.utcnow()
        return _steam_status.copy()

    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://steamcommunity.com/market/",
        })
        session.cookies.set("steamLoginSecure", settings.STEAM_LOGIN_SECURE, domain="steamcommunity.com")

        r = session.get(
            "https://steamcommunity.com/market/pricehistory/",
            params={"appid": 730, "market_hash_name": TEST_ITEM},
            timeout=15,
        )

        now = datetime.utcnow()
        _steam_status["last_checked"] = now

        if r.status_code == 429:
            _steam_status["status"] = "rate_limited"
            return _steam_status.copy()

        if r.status_code == 400:
            _steam_status["status"] = "expired"
            return _steam_status.copy()

        if r.status_code != 200:
            _steam_status["status"] = "error"
            return _steam_status.copy()

        data = r.json()
        if not isinstance(data, dict) or not data.get("success"):
            _steam_status["status"] = "expired"
            return _steam_status.copy()

        prices = data.get("prices", [])
        if not prices:
            _steam_status["status"] = "expired"
            return _steam_status.copy()

        # All good
        _steam_status["status"] = "ok"
        _steam_status["last_ok"] = now
        _steam_status["candle_count"] = len(prices)

    except requests.exceptions.Timeout:
        _steam_status["status"] = "timeout"
        _steam_status["last_checked"] = datetime.utcnow()
    except Exception as e:
        logger.error(f"Steam health check error: {e}")
        _steam_status["status"] = "error"
        _steam_status["last_checked"] = datetime.utcnow()

    return _steam_status.copy()


def get_steam_status() -> dict:
    """Return current in-memory status without making a new request."""
    return _steam_status.copy()


def run_scheduled_health_check() -> dict:
    """
    Called by the scheduler every 30 minutes.
    - Silent when healthy
    - On failure: sends Telegram alert + triggers cookie refresh script
    - On recovery: sends one restored message, back to silent
    """
    from app.services.telegram import (
        notify_steam_expired, notify_steam_rate_limited, notify_steam_restored
    )

    prev_status = _steam_status.get("status", "unknown")
    result = check_steam_health()
    new_status = result["status"]

    if new_status == "ok":
        # Only notify if recovering from a broken state
        if prev_status not in ("ok", "unknown"):
            notify_steam_restored()

    elif new_status in ("expired", "error", "timeout"):
        # Notify every check while broken + auto-refresh
        notify_steam_expired()
        _trigger_cookie_refresh()

    elif new_status == "rate_limited":
        # Only notify once when rate limiting starts, not every 30 mins
        if prev_status != "rate_limited":
            notify_steam_rate_limited()

    logger.info(f"Steam health check: {new_status} (was: {prev_status})")
    return result


def _trigger_cookie_refresh():
    """Run the refresh_cookie.sh script to automatically update the Steam cookie."""
    import subprocess, os
    script = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
        "refresh_cookie.sh"
    )
    # Try common locations
    candidates = [
        script,
        "/home/ratul/projects/CS2-Investment-Tracking/refresh_cookie.sh",
    ]
    for path in candidates:
        if os.path.exists(path):
            logger.info(f"Triggering cookie refresh: {path}")
            try:
                subprocess.Popen(
                    ["bash", path],
                    stdout=open("/var/log/steam_refresh.log", "a"),
                    stderr=subprocess.STDOUT,
                )
                logger.info("Cookie refresh script launched")
            except Exception as e:
                logger.error(f"Failed to launch refresh script: {e}")
            return
    logger.error("refresh_cookie.sh not found — cannot auto-refresh")
