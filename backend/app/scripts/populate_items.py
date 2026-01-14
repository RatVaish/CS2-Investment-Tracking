"""
Populate ALL CS2 items from ByMykel/CSGO-API with FULL metadata
Uses detailed endpoints to get collections, rarity, crates, etc.
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
    
    # Determine type
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

def extract_metadata(item_data):
    """Extract collection, rarity, and other metadata from item data"""
    metadata = {}
    
    # Collections - take first one if exists
    collections = item_data.get('collections', [])
    if collections:
        metadata['collection'] = collections[0].get('name')
    
    # Rarity
    rarity = item_data.get('rarity', {})
    if rarity:
        metadata['rarity'] = rarity.get('name')
    
    return metadata

def populate():
    """Populate database with full metadata"""
    logger.info("🚀 Starting comprehensive item population with metadata...")
    
    db = SessionLocal()
    item_manager = ItemManager(db)
    
    all_items = []
    
    try:
        # 1. SKINS (not grouped - includes all wears)
        logger.info("\n📦 Downloading skins...")
        skins = download_json("skins_not_grouped.json")
        for skin in skins:
            market_hash_name = skin.get('market_hash_name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            metadata = extract_metadata(skin)
            
            all_items.append({
                **parsed,
                'image_url': skin.get('image', ''),
                'collection': metadata.get('collection'),
                'rarity': metadata.get('rarity')
            })
        
        # 2. STICKERS
        logger.info("\n🎨 Downloading stickers...")
        stickers = download_json("stickers.json")
        for sticker in stickers:
            market_hash_name = sticker.get('market_hash_name') or sticker.get('name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            metadata = extract_metadata(sticker)
            
            all_items.append({
                **parsed,
                'image_url': sticker.get('image', ''),
                'collection': metadata.get('collection'),
                'rarity': metadata.get('rarity')
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
            parsed['item_type'] = 'agent'  # Force correct type
            metadata = extract_metadata(agent)
            
            all_items.append({
                **parsed,
                'image_url': agent.get('image', ''),
                'collection': metadata.get('collection'),
                'rarity': metadata.get('rarity')
            })
        
        # 5. KEYCHAINS
        logger.info("\n🔑 Downloading keychains...")
        keychains = download_json("keychains.json")
        for keychain in keychains:
            market_hash_name = keychain.get('market_hash_name') or keychain.get('name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            metadata = extract_metadata(keychain)
            
            all_items.append({
                **parsed,
                'image_url': keychain.get('image', ''),
                'collection': metadata.get('collection'),
                'rarity': metadata.get('rarity')
            })
        
        # 6. PATCHES
        logger.info("\n🏷️  Downloading patches...")
        patches = download_json("patches.json")
        for patch in patches:
            market_hash_name = patch.get('market_hash_name') or patch.get('name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            parsed['item_type'] = 'patch'  # Force correct type
            
            all_items.append({
                **parsed,
                'image_url': patch.get('image', ''),
                'collection': None,
                'rarity': patch.get('rarity', {}).get('name')
            })
        
        # 7. GRAFFITI
        logger.info("\n🎨 Downloading graffiti...")
        graffiti = download_json("graffiti.json")
        for graf in graffiti:
            market_hash_name = graf.get('market_hash_name') or graf.get('name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            
            all_items.append({
                **parsed,
                'image_url': graf.get('image', ''),
                'collection': None,
                'rarity': graf.get('rarity', {}).get('name')
            })
        
        # 8. MUSIC KITS
        logger.info("\n🎵 Downloading music kits...")
        music_kits = download_json("music_kits.json")
        for mk in music_kits:
            market_hash_name = mk.get('market_hash_name') or mk.get('name')
            if not market_hash_name:
                continue
            
            parsed = parse_item_name(market_hash_name)
            
            all_items.append({
                **parsed,
                'image_url': mk.get('image', ''),
                'collection': None,
                'rarity': mk.get('rarity', {}).get('name')
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
