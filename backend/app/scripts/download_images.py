"""
Download item images from CSFloat CDN and store locally

Run this script after populate_items.py to download all item images
and update database with local paths.
"""

import sys
import os
import httpx
from pathlib import Path
import re

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.session import SessionLocal
from app.services.item_manager import ItemManager
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Image storage directory
IMAGE_DIR = Path(__file__).parent.parent.parent / "public" / "images" / "items"


def sanitize_filename(name: str) -> str:
    """
    Convert item name to safe filename

    Example: "AK-47 | Redline (Field-Tested)" -> "ak47_redline_field-tested.png"
    """
    # Remove special characters, keep alphanumeric and spaces
    name = re.sub(r'[^\w\s-]', '', name.lower())
    # Replace spaces and multiple hyphens with single underscore
    name = re.sub(r'[-\s]+', '_', name)
    # Remove trailing/leading underscores
    name = name.strip('_')
    return f"{name}.png"


def download_image(url: str, save_path: Path, client: httpx.Client) -> bool:
    """
    Download image from URL and save to local path

    Args:
        url: Image URL
        save_path: Local path to save image
        client: HTTP client

    Returns:
        True if successful, False otherwise
    """
    try:
        response = client.get(url, timeout=30.0)
        response.raise_for_status()

        # Write image to file
        with open(save_path, 'wb') as f:
            f.write(response.content)

        return True

    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False


def download_all_images():
    """Download images for all items in database"""
    logger.info("Starting image download process...")

    # Create images directory if it doesn't exist
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Images will be saved to: {IMAGE_DIR}")

    db = SessionLocal()
    item_manager = ItemManager(db)
    client = httpx.Client(timeout=30.0)

    try:
        # Get all items
        items = item_manager.get_all_active_items()
        logger.info(f"Found {len(items)} items to process")

        downloaded_count = 0
        skipped_count = 0
        failed_count = 0

        for i, item in enumerate(items):
            try:
                # Skip if no image URL
                if not item.image_url:
                    skipped_count += 1
                    continue

                # Generate filename from item name
                filename = sanitize_filename(item.market_hash_name)
                save_path = IMAGE_DIR / filename

                # Skip if image already exists
                if save_path.exists():
                    # Update database with local path if needed
                    local_path = f"/images/items/{filename}"
                    if item.image_url != local_path:
                        from app.crud import item as crud_item
                        from app.schemas.item import ItemUpdate
                        crud_item.update_item(db, item.id, ItemUpdate(image_url=local_path))

                    skipped_count += 1
                    continue

                # Download image
                success = download_image(item.image_url, save_path, client)

                if success:
                    # Update database with local path
                    local_path = f"/images/items/{filename}"
                    from app.crud import item as crud_item
                    from app.schemas.item import ItemUpdate
                    crud_item.update_item(db, item.id, ItemUpdate(image_url=local_path))

                    downloaded_count += 1
                else:
                    failed_count += 1

                # Progress update every 100 items
                if (i + 1) % 100 == 0:
                    logger.info(f"Progress: {i + 1}/{len(items)} items processed...")
                    logger.info(f"  Downloaded: {downloaded_count}, Skipped: {skipped_count}, Failed: {failed_count}")

                # Rate limiting - be nice to CDN
                time.sleep(0.1)  # 10 requests per second max

            except Exception as e:
                logger.error(f"Error processing item {item.market_hash_name}: {e}")
                failed_count += 1
                continue

        logger.info(f"✅ Image download complete!")
        logger.info(f"   Downloaded: {downloaded_count}")
        logger.info(f"   Skipped (already exists): {skipped_count}")
        logger.info(f"   Failed: {failed_count}")
        logger.info(f"   Total: {len(items)}")
        logger.info(f"   Storage location: {IMAGE_DIR}")

    except Exception as e:
        logger.error(f"Image download failed: {e}")
        raise
    finally:
        client.close()
        db.close()


if __name__ == "__main__":
    download_all_images()
