"""
Populate items table with all CS2 items from CSFloat

Run this script once to initialize the items database.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.session import SessionLocal
from app.services.csfloat_client import CSFloatClient
from app.services.item_manager import ItemManager
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_item_name(market_hash_name: str) -> dict:
    """
    Parse item name to extract details

    Examples:
        "AK-47 | Redline (Field-Tested)" -> weapon_name="AK-47", skin_name="Redline", wear="Field-Tested"
        "AWP | Dragon Lore (Factory New)" -> weapon_name="AWP", skin_name="Dragon Lore", wear="Factory New"
        "Sticker | Katowice 2014" -> weapon_name=None, skin_name="Katowice 2014", wear=None
    """
    name = market_hash_name
    base_name = name
    wear = None
    weapon_name = None
    skin_name = None
    item_type = "other"
    is_stattrak = "StatTrak™" in name
    is_souvenir = "Souvenir" in name

    # Remove StatTrak and Souvenir prefixes
    name = name.replace("StatTrak™ ", "").replace("Souvenir ", "")

    # Extract wear if present
    wear_options = ["Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"]
    for wear_opt in wear_options:
        if f"({wear_opt})" in name:
            wear = wear_opt
            name = name.replace(f"({wear_opt})", "").strip()
            break

    # Determine item type and parse accordingly
    if " | " in name:
        # Weapon skin: "AK-47 | Redline"
        parts = name.split(" | ")
        weapon_name = parts[0].strip()
        skin_name = parts[1].strip() if len(parts) > 1 else None

        # Determine item type
        knives = ["Karambit", "Butterfly", "Bayonet", "M9", "Huntsman", "Falchion", "Bowie", "Flip", "Gut", "Daggers",
                  "Ursus", "Navaja", "Stiletto", "Talon", "Classic", "Paracord", "Survival", "Nomad", "Skeleton"]
        if any(knife in weapon_name for knife in knives):
            item_type = "knife"
        elif "Gloves" in weapon_name or "Wraps" in weapon_name or "Driver" in weapon_name or "Specialist" in weapon_name:
            item_type = "gloves"
        else:
            item_type = "skin"
    elif name.startswith("Sticker"):
        item_type = "sticker"
        skin_name = name.replace("Sticker | ", "").strip()
    elif "Case" in name:
        item_type = "case"
        skin_name = name
    elif "Agent" in name:
        item_type = "agent"
        skin_name = name
    elif "Patch" in name:
        item_type = "patch"
        skin_name = name
    elif "Music Kit" in name:
        item_type = "music_kit"
        skin_name = name
    elif "Graffiti" in name:
        item_type = "graffiti"
        skin_name = name
    else:
        skin_name = name

    # Set base name (name without wear)
    if " | " in market_hash_name:
        base_name = market_hash_name.split(" (")[0]
    else:
        base_name = market_hash_name.split(" (")[0]

    return {
        "market_hash_name": market_hash_name,
        "base_name": base_name,
        "weapon_name": weapon_name,
        "skin_name": skin_name,
        "wear": wear,
        "item_type": item_type,
        "is_stattrak": is_stattrak,
        "is_souvenir": is_souvenir
    }


def populate_items():
    """Fetch all items from CSFloat and populate database"""
    logger.info("Starting item population from CSFloat...")

    db = SessionLocal()
    csfloat = CSFloatClient()
    item_manager = ItemManager(db)

    try:
        # Fetch all items from CSFloat (this takes a while!)
        logger.info("Fetching all items from CSFloat (this may take 10-15 minutes)...")
        all_items = csfloat.get_all_items(batch_size=100)

        logger.info(f"Fetched {len(all_items)} unique items from CSFloat")

        # Process and insert into database
        created_count = 0
        skipped_count = 0

        for item_data in all_items:
            market_hash_name = item_data.get("market_hash_name")

            # Check if item already exists
            existing = item_manager.get_item_by_name(market_hash_name)
            if existing:
                skipped_count += 1
                continue

            # Parse item details
            parsed = parse_item_name(market_hash_name)

            # Add image URL
            parsed["image_url"] = item_data.get("image_url")

            # Create item in database
            try:
                item_manager.create_item(parsed)
                created_count += 1

                if created_count % 100 == 0:
                    logger.info(f"Created {created_count} items so far...")

            except Exception as e:
                logger.error(f"Failed to create item {market_hash_name}: {e}")
                continue

        logger.info(f"✅ Item population complete!")
        logger.info(f"   Created: {created_count}")
        logger.info(f"   Skipped (already exists): {skipped_count}")
        logger.info(f"   Total: {len(all_items)}")

    except Exception as e:
        logger.error(f"Item population failed: {e}")
        raise
    finally:
        csfloat.close()
        db.close()


if __name__ == "__main__":
    populate_items()
    