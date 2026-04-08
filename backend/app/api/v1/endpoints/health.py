"""
Health check endpoints.

GET /health          — basic liveness check (no auth)
GET /health/steam    — Steam cookie status (no auth, safe to expose)
POST /health/steam   — trigger an immediate Steam health check (no auth)
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("")
def health_check():
    """Basic liveness — used by Docker healthcheck and uptime monitors."""
    return {
        "status": "ok",
        "service": "Floatbase API",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/steam")
def get_steam_health():
    """
    Current Steam cookie status.
    Returns cached result from last check — does not make a live request.
    """
    from app.services.health import get_steam_status
    status = get_steam_status()
    return {
        "status": status["status"],
        "last_checked": status["last_checked"].isoformat() if status["last_checked"] else None,
        "last_ok": status["last_ok"].isoformat() if status["last_ok"] else None,
        "candle_count": status.get("candle_count"),
        "healthy": status["status"] == "ok",
    }


@router.post("/steam")
def trigger_steam_health_check():
    """
    Trigger an immediate Steam health check.
    Useful after updating the cookie — confirms it's working before waiting for
    the daily scheduled check.
    """
    from app.services.health import check_steam_health
    result = check_steam_health()
    return {
        "status": result["status"],
        "healthy": result["status"] == "ok",
        "last_checked": result["last_checked"].isoformat() if result["last_checked"] else None,
        "candle_count": result.get("candle_count"),
        "message": {
            "ok": "✅ Steam cookie is valid and returning price data",
            "expired": "🔴 Steam cookie is expired — update STEAM_LOGIN_SECURE in .env and rebuild",
            "rate_limited": "🟡 Steam is rate limiting requests — try again in a few minutes",
            "timeout": "🟡 Steam request timed out — may be temporary",
            "error": "⚠️ Unexpected error — check backend logs",
            "unconfigured": "⚠️ STEAM_LOGIN_SECURE not set in .env",
        }.get(result["status"], "Unknown status"),
    }
