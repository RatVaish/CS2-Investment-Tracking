"""
Populate ALL CS2 items with full metadata using multiple endpoints
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

BASE_URL = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en"

def download_json(endpoint):
    """Download JSON from endpoint"""
    try:
        url = f"{BASE_URL}/{endpoint}"
        logger.info(f"Downloading {endpoint}...")
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        data = response.json()
        logger.info(f"  ✅ Got {len(data)} items")
        return data
    except Exception as e:
        logger.error(f"  ❌ Failed: {e}")
        return []

def build_collection_map():
    """Build map of skin_id -> collection from skins.json (grouped version)"""
    logger.info("\n📚 Building collection map from skins.json...")
    skins_grouped = download_json("skins.json")
    
    collection_map = {}
    for skin in skins_grouped:
        skin_id = skin.get('id')
        collections = skin.get('collections', [])
        if skin_id and collections:
            # Take first collection
            collection_map[skin_id] = collections[0].get('name')
    
    logger.info(f"  ✅ Mapped {len(collection_map)} skins to collections")
    return collection_map

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
    
    clean_name = name.replace("StatTrak™ ", "").replace("Souvenir ", "")
    
    wear_options = ["Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"]
    for wear_opt in wear_options:
        if f"({wear_opt})" in clean_name:
            wear = wear_opt
            clean_name = clean_name.replace(f"({wear_opt})", "").strip()
            break
    
    if name.startswith("Sticker"):
        item_type = "sticker"
        skin_name = clean_name.replace("Sticker | ", "").replace("Sticker", "").strip()
    elif name.startswith("Patch"):
        item_type = "patch"
        skin_name = clean_name.replace("Patch | ", "").replace("Patch", "").strip()
    elif "Graffiti" in name:
        item_type = "graffiti"
        skin_name = clean_name.replace("Sealed Graffiti | ", "").strip()
    elif "Case" in name or "Capsule" in name:
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
        "is_souvenir": is_souvenir
    }

def populate():
    """Populate database with full metadata"""
    logger.info("🚀 Starting comprehensive item population...")
    
    # Build collection map FIRST
    collection_map = build_collection_map()
    
    db = SessionLocal()
    item_manager = ItemManager(db)
    
    all_items = []
    
    try:
        # 1. SKINS (not grouped - includes all wears + rarity)
        logger.info("\n📦 Downloading skins_not_grouped.json...")
        skins = download_json("skins_not_grouped.json")
        for skin in skins:
            market_hash_name = skin.get('market_hash_name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            
            # Get collection from map using skin_id
            skin_id = skin.get('skin_id')
            collection = collection_map.get(skin_id)
            
            # Get rarity
            rarity_obj = skin.get('rarity', {})
            rarity = rarity_obj.get('name') if rarity_obj else None
            
            all_items.append({
                **parsed,
                'image_url': skin.get('image', ''),
                'collection': collection,
                'rarity': rarity
            })
        
        # 2. STICKERS
        logger.info("\n🎨 Downloading stickers...")
        stickers = download_json("stickers.json")
        for sticker in stickers:
            market_hash_name = sticker.get('market_hash_name') or sticker.get('name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            parsed['item_type'] = 'sticker'  # Force correct type
            
            rarity_obj = sticker.get('rarity', {})
            rarity = rarity_obj.get('name') if rarity_obj else None
            
            # Stickers don't have collections in the data
            all_items.append({
                **parsed,
                'image_url': sticker.get('image', ''),
                'collection': None,
                'rarity': rarity
            })
        
        # 3. CASES
        logger.info("\n📦 Downloading cases...")
        cases = download_json("crates.json")
        for case in cases:
            market_hash_name = case.get('market_hash_name') or case.get('name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            
            all_items.append({
                **parsed,
                'image_url': case.get('image', ''),
                'collection': None,
                'rarity': None
            })
        
        # 4. AGENTS
        logger.info("\n👤 Downloading agents...")
        agents = download_json("agents.json")
        for agent in agents:
            market_hash_name = agent.get('market_hash_name') or agent.get('name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            parsed['item_type'] = 'agent'
            
            rarity_obj = agent.get('rarity', {})
            rarity = rarity_obj.get('name') if rarity_obj else None
            
            collections = agent.get('collections', [])
            collection = collections[0].get('name') if collections else None
            
            all_items.append({
                **parsed,
                'image_url': agent.get('image', ''),
                'collection': collection,
                'rarity': rarity
            })
        
        # 5. KEYCHAINS
        logger.info("\n🔑 Downloading keychains...")
        keychains = download_json("keychains.json")
        for keychain in keychains:
            market_hash_name = keychain.get('market_hash_name') or keychain.get('name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            
            rarity_obj = keychain.get('rarity', {})
            rarity = rarity_obj.get('name') if rarity_obj else None
            
            collections = keychain.get('collections', [])
            collection = collections[0].get('name') if collections else None
            
            all_items.append({
                **parsed,
                'image_url': keychain.get('image', ''),
                'collection': collection,
                'rarity': rarity
            })
        
        # 6. PATCHES
        logger.info("\n🏷️  Downloading patches...")
        patches = download_json("patches.json")
        for patch in patches:
            market_hash_name = patch.get('market_hash_name') or patch.get('name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            parsed['item_type'] = 'patch'
            
            rarity_obj = patch.get('rarity', {})
            rarity = rarity_obj.get('name') if rarity_obj else None
            
            all_items.append({
                **parsed,
                'image_url': patch.get('image', ''),
                'collection': None,
                'rarity': rarity
            })
        
        # 7. GRAFFITI
        logger.info("\n🎨 Downloading graffiti...")
        graffiti = download_json("graffiti.json")
        for graf in graffiti:
            market_hash_name = graf.get('market_hash_name') or graf.get('name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            
            rarity_obj = graf.get('rarity', {})
            rarity = rarity_obj.get('name') if rarity_obj else None
            
            all_items.append({
                **parsed,
                'image_url': graf.get('image', ''),
                'collection': None,
                'rarity': rarity
            })
        
        # 8. MUSIC KITS
        logger.info("\n🎵 Downloading music kits...")
        music_kits = download_json("music_kits.json")
        for mk in music_kits:
            market_hash_name = mk.get('market_hash_name') or mk.get('name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            
            rarity_obj = mk.get('rarity', {})
            rarity = rarity_obj.get('name') if rarity_obj else None
            
            all_items.append({
                **parsed,
                'image_url': mk.get('image', ''),
                'collection': None,
                'rarity': rarity
            })
        
        # INSERT INTO DATABASE
        logger.info(f"\n💾 Inserting {len(all_items)} items into database...")
        
        created_count = 0
        skipped_count = 0
        
        for item_data in all_items:
            market_hash_name = item_data['market_hash_name']
            
            existing = item_manager.get_item_by_name(market_hash_name)
            if existing:
                skipped_count += 1
                continue
            
            try:
                item_manager.create_item(item_data)
                created_count += 1
                
                if created_count % 1000 == 0:
                    logger.info(f"  📝 Created {created_count} items...")
            except Exception as e:
                logger.error(f"Failed to create {market_hash_name}: {e}")
        
        logger.info(f"\n✅ Population complete!")
        logger.info(f"   Created: {created_count}")
        logger.info(f"   Skipped: {skipped_count}")
        logger.info(f"   Total: {len(all_items)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    populate()
