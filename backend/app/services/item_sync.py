"""
Item Sync Service

Handles two jobs:
1. Initial population   — first-time load of all 27k+ CS2 items
2. Ongoing sync         — daily check for game updates via GitHub SHA comparison

Source: ByMykel/CSGO-API on GitHub
SHA check endpoint: https://api.github.com/repos/ByMykel/CSGO-API/commits/main
Data endpoint:      https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/

On each daily run:
- Fetch latest commit SHA from GitHub API
- Compare against last known SHA stored in item_sync_log
- If unchanged: log 'no_changes' and exit (fast, no data fetching)
- If changed: pull all item endpoints, upsert new/updated items,
  mark removed items is_active=False, log result
"""

import requests
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.item import Item
from app.models.item_sync_log import ItemSyncLog

logger = logging.getLogger(__name__)

BASE_URL = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en"
GITHUB_API_URL = "https://api.github.com/repos/ByMykel/CSGO-API/commits/main"


# ---------------------------------------------------------------------------
# GitHub SHA check
# ---------------------------------------------------------------------------

def get_latest_commit_sha() -> Optional[str]:
    """Fetch the latest commit SHA from the ByMykel/CSGO-API GitHub repo."""
    try:
        response = requests.get(
            GITHUB_API_URL,
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=15
        )
        response.raise_for_status()
        return response.json()["sha"]
    except Exception as e:
        logger.error(f"Failed to fetch GitHub commit SHA: {e}")
        return None


def get_last_synced_sha(db: Session) -> Optional[str]:
    """Get the commit SHA from the most recent successful sync."""
    last = db.query(ItemSyncLog).filter(
        ItemSyncLog.status.in_(["success", "partial"])
    ).order_by(ItemSyncLog.synced_at.desc()).first()

    return last.commit_sha if last else None


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def download_json(endpoint: str) -> list:
    """Download a JSON endpoint from the ByMykel API."""
    try:
        url = f"{BASE_URL}/{endpoint}"
        logger.info(f"Downloading {endpoint}...")
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        data = response.json()
        logger.info(f"  Got {len(data)} items from {endpoint}")
        return data
    except Exception as e:
        logger.error(f"Failed to download {endpoint}: {e}")
        return []


def build_collection_map() -> dict:
    """Build map of skin_id -> collection name from skins.json."""
    skins_grouped = download_json("skins.json")
    collection_map = {}
    for skin in skins_grouped:
        skin_id = skin.get("id")
        collections = skin.get("collections", [])
        if skin_id and collections:
            collection_map[skin_id] = collections[0].get("name")
    logger.info(f"Mapped {len(collection_map)} skins to collections")
    return collection_map


# ---------------------------------------------------------------------------
# Item name parsing
# ---------------------------------------------------------------------------

def parse_item_name(market_hash_name: str) -> dict:
    """
    Parse a CS2 market_hash_name into structured components.

    Examples:
        "AK-47 | Redline (Field-Tested)"
            → weapon_name="AK-47", skin_name="Redline", wear="Field-Tested", item_type="skin"
        "StatTrak™ AWP | Asiimov (Factory New)"
            → is_stattrak=True, weapon_name="AWP", skin_name="Asiimov", wear="Factory New"
        "★ Karambit | Doppler (Factory New)"
            → item_type="knife", weapon_name="Karambit", skin_name="Doppler"
        "Sticker | Katowice 2014"
            → item_type="sticker", skin_name="Katowice 2014"
    """
    name = market_hash_name
    is_stattrak = "StatTrak™" in name
    is_souvenir = "Souvenir" in name

    clean_name = name.replace("StatTrak™ ", "").replace("Souvenir ", "")

    # Extract wear
    wear = None
    wear_options = ["Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"]
    for wear_opt in wear_options:
        if f"({wear_opt})" in clean_name:
            wear = wear_opt
            clean_name = clean_name.replace(f"({wear_opt})", "").strip()
            break

    # Determine item type and parse components
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
    elif "Charm" in name or clean_name.startswith("Charm"):
        item_type = "keychain"
        skin_name = clean_name
    elif "Music Kit" in name:
        item_type = "music_kit"
        skin_name = clean_name
    elif " | " in clean_name:
        parts = clean_name.split(" | ")
        weapon_name = parts[0].strip()
        skin_name = parts[1].strip() if len(parts) > 1 else None

        if "★" in weapon_name:
            if "Gloves" in weapon_name or "Wraps" in weapon_name:
                item_type = "gloves"
            else:
                item_type = "knife"
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


# ---------------------------------------------------------------------------
# Build full item list from all endpoints
# ---------------------------------------------------------------------------

def fetch_all_items() -> list[dict]:
    """
    Download all CS2 item types from ByMykel API and return
    a unified list of item dicts ready for DB upsert.
    """
    collection_map = build_collection_map()
    all_items = []

    # 1. Skins
    skins = download_json("skins_not_grouped.json")
    for skin in skins:
        mhn = skin.get("market_hash_name")
        if not mhn:
            continue
        parsed = parse_item_name(mhn)
        rarity_obj = skin.get("rarity", {})
        skin_id = skin.get("skin_id")
        all_items.append({
            **parsed,
            "image_url": skin.get("image", ""),
            "collection": collection_map.get(skin_id),
            "rarity": rarity_obj.get("name") if rarity_obj else None,
        })

    # 2. Stickers
    stickers = download_json("stickers.json")
    for sticker in stickers:
        mhn = sticker.get("market_hash_name") or sticker.get("name")
        if not mhn:
            continue
        parsed = parse_item_name(mhn)
        parsed["item_type"] = "sticker"
        rarity_obj = sticker.get("rarity", {})
        all_items.append({
            **parsed,
            "image_url": sticker.get("image", ""),
            "collection": None,
            "rarity": rarity_obj.get("name") if rarity_obj else None,
        })

    # 3. Cases & Capsules
    cases = download_json("crates.json")
    for case in cases:
        mhn = case.get("market_hash_name") or case.get("name")
        if not mhn:
            continue
        parsed = parse_item_name(mhn)
        all_items.append({
            **parsed,
            "image_url": case.get("image", ""),
            "collection": None,
            "rarity": None,
        })

    # 4. Agents
    agents = download_json("agents.json")
    for agent in agents:
        mhn = agent.get("market_hash_name") or agent.get("name")
        if not mhn:
            continue
        parsed = parse_item_name(mhn)
        parsed["item_type"] = "agent"
        rarity_obj = agent.get("rarity", {})
        collections = agent.get("collections", [])
        all_items.append({
            **parsed,
            "image_url": agent.get("image", ""),
            "collection": collections[0].get("name") if collections else None,
            "rarity": rarity_obj.get("name") if rarity_obj else None,
        })

    # 5. Keychains
    keychains = download_json("keychains.json")
    for keychain in keychains:
        mhn = keychain.get("market_hash_name") or keychain.get("name")
        if not mhn:
            continue
        parsed = parse_item_name(mhn)
        rarity_obj = keychain.get("rarity", {})
        collections = keychain.get("collections", [])
        all_items.append({
            **parsed,
            "image_url": keychain.get("image", ""),
            "collection": collections[0].get("name") if collections else None,
            "rarity": rarity_obj.get("name") if rarity_obj else None,
        })

    # 6. Patches
    patches = download_json("patches.json")
    for patch in patches:
        mhn = patch.get("market_hash_name") or patch.get("name")
        if not mhn:
            continue
        parsed = parse_item_name(mhn)
        parsed["item_type"] = "patch"
        rarity_obj = patch.get("rarity", {})
        all_items.append({
            **parsed,
            "image_url": patch.get("image", ""),
            "collection": None,
            "rarity": rarity_obj.get("name") if rarity_obj else None,
        })

    # 7. Graffiti
    graffiti = download_json("graffiti.json")
    for graf in graffiti:
        mhn = graf.get("market_hash_name") or graf.get("name")
        if not mhn:
            continue
        parsed = parse_item_name(mhn)
        rarity_obj = graf.get("rarity", {})
        all_items.append({
            **parsed,
            "image_url": graf.get("image", ""),
            "collection": None,
            "rarity": rarity_obj.get("name") if rarity_obj else None,
        })

    # 8. Music Kits
    music_kits = download_json("music_kits.json")
    for mk in music_kits:
        mhn = mk.get("market_hash_name") or mk.get("name")
        if not mhn:
            continue
        parsed = parse_item_name(mhn)
        rarity_obj = mk.get("rarity", {})
        all_items.append({
            **parsed,
            "image_url": mk.get("image", ""),
            "collection": None,
            "rarity": rarity_obj.get("name") if rarity_obj else None,
        })

    logger.info(f"Total items fetched from all endpoints: {len(all_items)}")
    return all_items


# ---------------------------------------------------------------------------
# DB upsert logic
# ---------------------------------------------------------------------------

def upsert_items(db: Session, all_items: list[dict]) -> dict:
    """
    Upsert items into the database.

    - New items: inserted
    - Existing items: image_url, collection, rarity updated if changed
    - Items in DB but not in source: marked is_active=False

    Returns stats dict.
    """
    now = datetime.utcnow()
    stats = {"added": 0, "updated": 0, "deactivated": 0, "errors": 0}

    # Build a set of all market_hash_names from source
    source_names = {item["market_hash_name"] for item in all_items}

    # Fetch all existing items from DB into memory (27k rows, small)
    existing_items = {
        item.market_hash_name: item
        for item in db.query(Item).all()
    }

    # Upsert each item from source
    for item_data in all_items:
        mhn = item_data["market_hash_name"]
        try:
            if mhn in existing_items:
                existing = existing_items[mhn]
                changed = False

                # Update fields that may change when the game updates
                if item_data.get("image_url") and existing.image_url != item_data["image_url"]:
                    existing.image_url = item_data["image_url"]
                    changed = True
                if item_data.get("collection") and existing.collection != item_data["collection"]:
                    existing.collection = item_data["collection"]
                    changed = True
                if item_data.get("rarity") and existing.rarity != item_data["rarity"]:
                    existing.rarity = item_data["rarity"]
                    changed = True

                # Re-activate if it was previously deactivated
                if not existing.is_active:
                    existing.is_active = True
                    changed = True

                if changed:
                    existing.last_synced_at = now
                    existing.updated_at = now
                    stats["updated"] += 1
            else:
                # New item
                new_item = Item(
                    **item_data,
                    is_active=True,
                    last_synced_at=now,
                )
                db.add(new_item)
                stats["added"] += 1

            # Commit in batches to avoid giant transactions
            if (stats["added"] + stats["updated"]) % 500 == 0:
                db.commit()

        except Exception as e:
            logger.error(f"Error upserting {mhn}: {e}")
            stats["errors"] += 1

    # Mark items no longer in source as inactive
    for mhn, existing in existing_items.items():
        if mhn not in source_names and existing.is_active:
            existing.is_active = False
            existing.updated_at = now
            stats["deactivated"] += 1

    db.commit()
    return stats


# ---------------------------------------------------------------------------
# Main sync entry points
# ---------------------------------------------------------------------------

def run_sync(db: Session, force: bool = False) -> dict:
    """
    Main sync entry point — called by the daily scheduler.

    Args:
        db:    SQLAlchemy session
        force: If True, skip SHA check and always do a full sync.
               Use this for the initial population run.

    Returns:
        Stats dict with added/updated/deactivated counts.
    """
    logger.info("Starting item sync check...")

    latest_sha = get_latest_commit_sha()
    last_sha = get_last_synced_sha(db)

    if not force and latest_sha and latest_sha == last_sha:
        logger.info(f"No changes detected (SHA: {latest_sha[:8]}). Skipping sync.")
        log = ItemSyncLog(
            commit_sha=latest_sha,
            previous_sha=last_sha,
            items_added=0,
            items_updated=0,
            items_deactivated=0,
            status="no_changes",
        )
        db.add(log)
        db.commit()
        return {"status": "no_changes", "sha": latest_sha}

    if not latest_sha:
        logger.warning("Could not fetch latest SHA — running sync anyway")

    logger.info(f"Changes detected. Previous SHA: {last_sha[:8] if last_sha else 'none'} → New SHA: {latest_sha[:8] if latest_sha else 'unknown'}")
    logger.info("Fetching all items from ByMykel API...")

    try:
        all_items = fetch_all_items()

        if not all_items:
            log = ItemSyncLog(
                commit_sha=latest_sha,
                previous_sha=last_sha,
                status="failed",
                error_msg="fetch_all_items returned empty list",
            )
            db.add(log)
            db.commit()
            return {"status": "failed", "error": "Empty item list"}

        logger.info(f"Upserting {len(all_items)} items...")
        stats = upsert_items(db, all_items)

        status = "success" if stats["errors"] == 0 else "partial"
        log = ItemSyncLog(
            commit_sha=latest_sha,
            previous_sha=last_sha,
            items_added=stats["added"],
            items_updated=stats["updated"],
            items_deactivated=stats["deactivated"],
            status=status,
            error_msg=f"{stats['errors']} errors" if stats["errors"] else None,
        )
        db.add(log)
        db.commit()

        logger.info(
            f"Sync complete — added: {stats['added']}, "
            f"updated: {stats['updated']}, "
            f"deactivated: {stats['deactivated']}, "
            f"errors: {stats['errors']}"
        )
        return {"status": status, **stats}

    except Exception as e:
        logger.error(f"Sync failed with exception: {e}")
        log = ItemSyncLog(
            commit_sha=latest_sha,
            previous_sha=last_sha,
            status="failed",
            error_msg=str(e),
        )
        db.add(log)
        db.commit()
        return {"status": "failed", "error": str(e)}
