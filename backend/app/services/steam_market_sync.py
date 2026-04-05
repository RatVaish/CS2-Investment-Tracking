"""
Steam Market Item Sync Service

Discovers CS2 items directly from the Steam Community Market.
No dependency on ByMykel or any third-party repo.

Correct endpoint (norender=1 required for JSON results):
    GET https://steamcommunity.com/market/search/render/
        ?appid=730
        &norender=1
        &sort_column=name
        &sort_dir=asc
        &start={offset}
        &count=100

Response structure (with norender=1):
    {
        "success": true,
        "total_count": 31105,
        "results": [
            {
                "hash_name": "AK-47 | Redline (Field-Tested)",   <- market_hash_name
                "asset_description": {
                    "classid": "310776631",
                    "icon_url": "...",
                    "type": "Classified Rifle",
                    "commodity": 0,                              <- 1 = fungible item
                    "market_hash_name": "AK-47 | Redline (Field-Tested)"
                }
            }
        ]
    }

Note: tags[] is empty on this endpoint. We parse item type from
hash_name (same logic as item_sync.py) and commodity from asset_description.
"""

import time
import logging
import requests
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.item_sync_log import ItemSyncLog

logger = logging.getLogger(__name__)

STEAM_MARKET_URL = "https://steamcommunity.com/market/search/render/"
STEAM_IMAGE_CDN = "https://community.akamai.steamstatic.com/economy/image/"
PAGE_SIZE = 100
REQUEST_DELAY = 2.0


# ---------------------------------------------------------------------------
# Item name parsing
# ---------------------------------------------------------------------------

def parse_item_name(market_hash_name: str) -> dict:
    """Parse a CS2 market_hash_name into structured components."""
    name = market_hash_name
    is_stattrak = "StatTrak\u2122" in name
    is_souvenir = "Souvenir" in name

    clean_name = name.replace("StatTrak\u2122 ", "").replace("Souvenir ", "")

    wear = None
    for wear_opt in ["Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"]:
        if f"({wear_opt})" in clean_name:
            wear = wear_opt
            clean_name = clean_name.replace(f"({wear_opt})", "").strip()
            break

    weapon_name = None
    skin_name = None
    item_type = "other"

    if name.startswith("Sticker"):
        item_type = "sticker"
        skin_name = clean_name.replace("Sticker | ", "").replace("Sticker", "").strip()
    elif name.startswith("Patch"):
        item_type = "patch"
        skin_name = clean_name.replace("Patch | ", "").replace("Patch", "").strip()
    elif "Graffiti" in name:
        item_type = "graffiti"
        skin_name = clean_name.replace("Sealed Graffiti | ", "").strip()
    elif "Case" in name or "Capsule" in name or "Package" in name:
        item_type = "case"
        skin_name = clean_name
    elif "Charm" in name:
        item_type = "keychain"
        skin_name = clean_name
    elif "Music Kit" in name:
        item_type = "music_kit"
        skin_name = clean_name
    elif " | " in clean_name:
        parts = clean_name.split(" | ")
        weapon_name = parts[0].strip()
        skin_name = parts[1].strip() if len(parts) > 1 else None
        if "\u2605" in weapon_name:
            item_type = "gloves" if ("Gloves" in weapon_name or "Wraps" in weapon_name) else "knife"
        else:
            item_type = "skin"
    else:
        skin_name = clean_name

    base_name = market_hash_name.split(" (")[0]

    return {
        "market_hash_name": market_hash_name,
        "base_name": base_name,
        "weapon_name": weapon_name,
        "skin_name": skin_name,
        "wear": wear,
        "item_type": item_type,
        "is_stattrak": is_stattrak,
        "is_souvenir": is_souvenir,
    }


def parse_image_url(icon_url: str) -> Optional[str]:
    if not icon_url:
        return None
    return f"{STEAM_IMAGE_CDN}{icon_url}"


# ---------------------------------------------------------------------------
# Steam Market pagination
# ---------------------------------------------------------------------------

def fetch_page(start: int, session: requests.Session) -> Optional[dict]:
    """Fetch one page of Steam Market CS2 listings."""
    params = {
        "appid": 730,
        "norender": 1,
        "sort_column": "name",
        "sort_dir": "asc",
        "start": start,
        "count": PAGE_SIZE,
    }
    try:
        response = session.get(STEAM_MARKET_URL, params=params, timeout=30)

        if response.status_code == 429:
            logger.warning(f"Rate limited at offset {start}. Waiting 60s...")
            time.sleep(60)
            response = session.get(STEAM_MARKET_URL, params=params, timeout=30)

        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            logger.error(f"Steam returned success=false at offset {start}")
            return None

        return data

    except requests.exceptions.Timeout:
        logger.error(f"Timeout at offset {start}")
        return None
    except Exception as e:
        logger.error(f"Error at offset {start}: {e}")
        return None


def fetch_all_steam_items() -> list:
    """Paginate through all CS2 Steam Market listings."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })

    logger.info("Fetching first page to get total item count...")
    first_page = fetch_page(0, session)
    if not first_page:
        logger.error("Failed to fetch first Steam Market page")
        return []

    total_count = first_page.get("total_count", 0)
    logger.info(f"Steam Market reports {total_count} total CS2 listings")

    all_items = []

    for start in range(0, total_count, PAGE_SIZE):
        data = first_page if start == 0 else None

        if start > 0:
            time.sleep(REQUEST_DELAY)
            data = fetch_page(start, session)

        if not data:
            logger.warning(f"Skipping page at offset {start}")
            continue

        results = data.get("results", [])
        for result in results:
            mhn = result.get("hash_name")
            if not mhn:
                continue

            asset = result.get("asset_description", {})
            icon_url = asset.get("icon_url", "")
            commodity = asset.get("commodity", 0)

            parsed = parse_item_name(mhn)
            parsed["image_url"] = parse_image_url(icon_url)
            parsed["is_commodity"] = bool(commodity)
            all_items.append(parsed)

        if start % 5000 == 0 and start > 0:
            logger.info(f"Progress: {start}/{total_count} processed, {len(all_items)} parsed")

    logger.info(f"Fetched and parsed {len(all_items)} items from Steam Market")
    return all_items


# ---------------------------------------------------------------------------
# DB upsert
# ---------------------------------------------------------------------------

def upsert_steam_items(db: Session, all_items: list) -> dict:
    """Insert new items from Steam Market. Skip existing ones."""
    now = datetime.utcnow()
    stats = {"added": 0, "skipped": 0, "errors": 0}

    existing_names = {
        row[0] for row in db.query(Item.market_hash_name).all()
    }

    new_items = [i for i in all_items if i["market_hash_name"] not in existing_names]
    logger.info(
        f"{len(new_items)} new items to insert, "
        f"{len(all_items) - len(new_items)} already exist"
    )

    for item_data in new_items:
        try:
            new_item = Item(
                market_hash_name=item_data["market_hash_name"],
                base_name=item_data.get("base_name") or item_data["market_hash_name"],
                item_type=item_data.get("item_type", "other"),
                weapon_name=item_data.get("weapon_name"),
                skin_name=item_data.get("skin_name"),
                wear=item_data.get("wear"),
                image_url=item_data.get("image_url"),
                is_stattrak=item_data.get("is_stattrak", False),
                is_souvenir=item_data.get("is_souvenir", False),
                is_commodity=item_data.get("is_commodity", False),
                is_active=True,
                last_synced_at=now,
            )
            db.add(new_item)
            stats["added"] += 1

            if stats["added"] % 500 == 0:
                db.commit()
                logger.info(f"Inserted {stats['added']} new items...")

        except Exception as e:
            logger.error(f"Error inserting {item_data.get('market_hash_name')}: {e}")
            stats["errors"] += 1

    db.commit()
    stats["skipped"] = len(all_items) - len(new_items)
    return stats


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_steam_market_sync(db: Session) -> dict:
    """
    Run a full Steam Market sync.
    Called by daily scheduler and manual admin trigger.
    Full crawl takes ~15 minutes for ~31k items at 2s/page.
    """
    logger.info("Starting Steam Market item sync...")
    start_time = datetime.utcnow()

    try:
        all_items = fetch_all_steam_items()

        if not all_items:
            log = ItemSyncLog(
                source="steam_market",
                status="failed",
                error_msg="fetch_all_steam_items returned empty list",
            )
            db.add(log)
            db.commit()
            return {"status": "failed", "error": "Empty item list from Steam Market"}

        stats = upsert_steam_items(db, all_items)
        status = "success" if stats["errors"] == 0 else "partial"

        log = ItemSyncLog(
            source="steam_market",
            items_added=stats["added"],
            items_updated=0,
            items_deactivated=0,
            status=status,
            error_msg=f"{stats['errors']} errors" if stats["errors"] else None,
        )
        db.add(log)
        db.commit()

        duration = (datetime.utcnow() - start_time).seconds
        logger.info(
            f"Steam Market sync complete in {duration}s — "
            f"added: {stats['added']}, skipped: {stats['skipped']}, errors: {stats['errors']}"
        )
        return {"status": status, **stats}

    except Exception as e:
        logger.error(f"Steam Market sync failed: {e}")
        log = ItemSyncLog(
            source="steam_market",
            status="failed",
            error_msg=str(e),
        )
        db.add(log)
        db.commit()
        return {"status": "failed", "error": str(e)}
