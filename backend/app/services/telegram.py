"""
Telegram notification service.

Sends alerts to your personal Telegram chat when things need attention.
Currently used for:
  - Steam cookie expiry / health check failures
  - Can be extended for new user signups, revenue milestones, errors, etc.
"""

import logging
import requests
from app.core.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """
    Send a message to the configured Telegram chat.
    Returns True if sent successfully, False otherwise.
    Silent on failure — never let notifications crash the app.
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.debug("Telegram not configured, skipping notification")
        return False

    try:
        url = TELEGRAM_API.format(token=settings.TELEGRAM_BOT_TOKEN)
        resp = requests.post(url, json={
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
        }, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")
        return False


# ─── Pre-built message templates ─────────────────────────────────────────────

def notify_steam_expired():
    send_message(
        "🔴 <b>Floatbase — Steam cookie expired</b>\n\n"
        "Price history charts will not load for new investments.\n\n"
        "<b>Fix:</b>\n"
        "1. Go to steamcommunity.com in Chrome\n"
        "2. DevTools → Application → Cookies\n"
        "3. Copy <code>steamLoginSecure</code>\n"
        "4. Update <code>STEAM_LOGIN_SECURE</code> in <code>.env</code>\n"
        "5. Run <code>docker compose up --build -d</code>"
    )


def notify_steam_rate_limited():
    send_message(
        "🟡 <b>Floatbase — Steam rate limited</b>\n\n"
        "Price history requests are being throttled by Steam. "
        "The backfill queue will retry automatically — no action needed unless this persists."
    )


def notify_steam_restored():
    send_message(
        "🟢 <b>Floatbase — Steam connection restored</b>\n\n"
        "Price history is fetching successfully again."
    )


def notify_steam_ok(candle_count: int):
    """Silent success — only call this manually for testing, not on every check."""
    send_message(
        f"✅ <b>Floatbase — Steam health OK</b>\n\n"
        f"Cookie valid · {candle_count} data points returned"
    )


def notify_error(context: str, error: str):
    send_message(
        f"⚠️ <b>Floatbase — Error</b>\n\n"
        f"<b>Context:</b> {context}\n"
        f"<b>Error:</b> <code>{error[:200]}</code>"
    )
