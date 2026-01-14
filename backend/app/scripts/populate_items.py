"""
Populate ALL CS2 items from ByMykel/CSGO-API
Downloads all.json which contains every CS2 item
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.session import SessionLocal
from app.services.item_manager import ItemManager
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALL_ITEMS_URL = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/all.json"

def parse_item_name(market_hash_name: str) -> dict:
    """Parse market hash name into components"""
    name = market_hash_name
    base_name = name
    wear = None
    weapon_name = None
    skin_name = None
    item_type = "other"
    is_stattrak = "StatTrak™" in name
    is_souvenir = "Souvenir" in name
    
    name = name.replace("StatTrak™ ", "").replace("Souvenir ", "")
    
    wear_options = ["Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"]
    for wear_opt in wear_options:
        if f"({wear_opt})" in name:
            wear = wear_opt
            name = name.replace(f"({wear_opt})", "").strip()
            break
    
    if " | " in name:
        parts = name.split(" | ")
        weapon_name = parts[0].strip()
        skin_name = parts[1].strip() if len(parts) > 1 else None
        
        if "★" in weapon_name:
            if "Gloves" in weapon_name or "Wraps" in weapon_name:
                item_type = "gloves"
            else:
                item_type = "knife"
        else:
            item_type = "skin"
    elif "Sticker" in name:
        item_type = "sticker"
        skin_name = name.replace("Sticker | ", "").strip()
    elif "Case" in name:
        item_type = "case"
        skin_name = name
    elif "Agent" in name or "| The " in name:
        item_type = "agent"
        skin_name = name
    elif "Charm" in name:
        item_type = "keychain"
        skin_name = name
    elif "Patch" in name:
        item_type = "patch"
        skin_name = name
    elif "Graffiti" in name:
        item_type = "graffiti"
        skin_name = name
    elif "Music Kit" in name:
        item_type = "music_kit"
        skin_name = name
    else:
        skin_name = name
    
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

def populate():
    """Populate database with ALL CS2 items from all.json"""
    logger.info("Downloading all CS2 items from ByMykel API...")
    
    try:
        response = requests.get(ALL_ITEMS_URL, timeout=120)
        response.raise_for_status()
        all_items_dict = response.json()
        
        logger.info(f"Downloaded {len(all_items_dict)} total items")
        
    except Exception as e:
        logger.error(f"Failed to download all.json: {e}")
        return
    
    db = SessionLocal()
    item_manager = ItemManager(db)
    
    try:
        logger.info("Processing items...")
        
        created_count = 0
        skipped_count = 0
        
        # all.json is a dict with item IDs as keys
        for item_id, item_data in all_items_dict.items():
            market_hash_name = item_data.get('market_hash_name') or item_data.get('name')
            
            if not market_hash_name:
                continue
            
            # Check if exists
            existing = item_manager.get_item_by_name(market_hash_name)
            if existing:
                skipped_count += 1
                continue
            
            # Parse and create
            parsed = parse_item_name(market_hash_name)
            parsed['image_url'] = item_data.get('image', '')
            
            try:
                item_manager.create_item(parsed)
                created_count += 1
                
                if created_count % 1000 == 0:
                    logger.info(f"  Created {created_count} items...")
            except Exception as e:
                logger.error(f"Failed to create {market_hash_name}: {e}")
        
        logger.info(f"\n✅ Population complete!")
        logger.info(f"   Created: {created_count}")
        logger.info(f"   Skipped: {skipped_count}")
        logger.info(f"   Total items in file: {len(all_items_dict)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    populate()
