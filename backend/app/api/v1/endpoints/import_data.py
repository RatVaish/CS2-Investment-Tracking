"""
Import endpoints — Steam inventory & CSV import (Pro only).
"""

import csv
import io
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
import httpx

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.item import Item
from app.models.investment import Investment
from app.crud.investment import count_active_investments

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_pro(user: User):
    if user.tier != "pro":
        raise HTTPException(status_code=403, detail="This feature requires a Pro subscription.")


def _find_item_by_name(db: Session, market_hash_name: str) -> Optional[Item]:
    return db.query(Item).filter(
        Item.market_hash_name == market_hash_name
    ).first()


# ---------------------------------------------------------------------------
# Steam Inventory Import
# ---------------------------------------------------------------------------

@router.get("/steam-inventory")
def fetch_steam_inventory(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Fetch the user's public CS2 Steam inventory.
    Returns items that exist in our database, ready for import preview.
    Pro only.
    """
    _require_pro(current_user)

    if not current_user.steam_id:
        raise HTTPException(
            status_code=400,
            detail="No Steam account linked. Connect Steam from your profile settings."
        )

    steam_id = current_user.steam_id
    url = f"https://steamcommunity.com/inventory/{steam_id}/730/2?l=english&count=2000"

    try:
        resp = httpx.get(url, timeout=15, headers={"User-Agent": "Floatbase/1.0"})
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Steam inventory request timed out. Try again.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to reach Steam: {str(e)}")

    if resp.status_code == 403:
        raise HTTPException(
            status_code=400,
            detail="Your Steam inventory is set to private. Make it public in Steam privacy settings."
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Steam returned an unexpected response.")

    data = resp.json()
    if not data.get("success"):
        raise HTTPException(status_code=400, detail="Steam inventory unavailable or private.")

    assets = {a["assetid"]: a for a in data.get("assets", [])}
    descriptions = {
        f"{d['classid']}_{d['instanceid']}": d
        for d in data.get("descriptions", [])
    }

    matched = []
    skipped_count = 0

    for asset_id, asset in assets.items():
        key = f"{asset['classid']}_{asset['instanceid']}"
        desc = descriptions.get(key, {})
        name = desc.get("market_hash_name", "")

        if not name:
            skipped_count += 1
            continue

        # Only tradable items
        if not desc.get("tradable", 0):
            skipped_count += 1
            continue

        # Look up in our DB
        item = _find_item_by_name(db, name)

        matched.append({
            "asset_id": asset_id,
            "market_hash_name": name,
            "item_id": item.id if item else None,
            "image_url": item.image_url if item else f"https://community.cloudflare.steamstatic.com/economy/image/{desc.get('icon_url', '')}",
            "item_type": item.item_type if item else "unknown",
            "rarity": item.rarity if item else None,
            "wear": item.wear if item else None,
            "is_stattrak": item.is_stattrak if item else ("StatTrak" in name),
            "in_our_db": item is not None,
        })

    # Get existing asset IDs to flag already-imported items
    existing_asset_ids = set(
        r[0] for r in db.query(Investment.steam_asset_id).filter(
            Investment.user_id == current_user.id,
            Investment.steam_asset_id.isnot(None),
        ).all()
    )

    for m in matched:
        m["already_imported"] = m["asset_id"] in existing_asset_ids

    return {
        "steam_id": steam_id,
        "total_assets": len(assets),
        "matched": len(matched),
        "skipped": skipped_count,
        "items": matched,
    }


@router.post("/steam-inventory")
def import_steam_inventory(
        payload: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Import selected Steam inventory items as investments.
    Payload: { items: [{ asset_id, item_id, purchase_price, quantity, purchase_date? }] }
    Pro only.
    """
    _require_pro(current_user)

    items_to_import = payload.get("items", [])
    if not items_to_import:
        raise HTTPException(status_code=400, detail="No items provided.")

    created = []
    errors = []

    for entry in items_to_import:
        item_id = entry.get("item_id")
        asset_id = entry.get("asset_id")
        purchase_price = entry.get("purchase_price", 0)
        quantity = entry.get("quantity", 1)
        purchase_date = entry.get("purchase_date")

        if not item_id:
            errors.append({"asset_id": asset_id, "error": "Item not in our database"})
            continue

        # Check duplicate by asset_id
        existing = db.query(Investment).filter(
            Investment.user_id == current_user.id,
            Investment.steam_asset_id == str(asset_id),
        ).first()
        if existing:
            errors.append({"asset_id": asset_id, "error": "Already imported"})
            continue

        from datetime import datetime as dt
        pd = None
        if purchase_date:
            try:
                pd = dt.fromisoformat(purchase_date)
            except Exception:
                pd = None

        inv = Investment(
            user_id=current_user.id,
            item_id=item_id,
            purchase_price=float(purchase_price),
            quantity=int(quantity),
            purchase_date=pd,
            status="active",
            import_source="steam",
            steam_asset_id=str(asset_id),
        )
        db.add(inv)
        created.append({"asset_id": asset_id, "item_id": item_id})

    db.commit()
    return {
        "imported": len(created),
        "errors": errors,
        "items": created,
    }


# ---------------------------------------------------------------------------
# CSV Import
# ---------------------------------------------------------------------------

@router.post("/csv")
async def import_csv(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Import investments from CSV file.
    Expected columns: market_hash_name, purchase_price, quantity, purchase_date (optional), notes (optional)
    Pro only.
    """
    _require_pro(current_user)

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    contents = await file.read()
    try:
        text = contents.decode("utf-8-sig")  # handles BOM from Excel
    except UnicodeDecodeError:
        text = contents.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))

    # Normalise headers — strip whitespace and lowercase
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV appears empty or has no headers.")

    required = {"market_hash_name", "purchase_price", "quantity"}
    headers = {h.strip().lower() for h in reader.fieldnames}
    missing = required - headers
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {', '.join(missing)}. "
                   f"Required: market_hash_name, purchase_price, quantity"
        )

    created = []
    errors = []
    from datetime import datetime as dt

    for i, row in enumerate(reader, start=2):  # row 1 = header
        # Normalise row keys
        row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

        name = row.get("market_hash_name", "").strip()
        if not name:
            errors.append({"row": i, "error": "Empty market_hash_name"})
            continue

        try:
            purchase_price = float(row.get("purchase_price", 0))
            quantity = int(row.get("quantity", 1))
        except ValueError:
            errors.append({"row": i, "name": name, "error": "Invalid price or quantity"})
            continue

        if purchase_price <= 0 or quantity < 1:
            errors.append({"row": i, "name": name, "error": "Price must be >0 and quantity >=1"})
            continue

        item = _find_item_by_name(db, name)
        if not item:
            errors.append({"row": i, "name": name, "error": "Item not found in our database"})
            continue

        purchase_date = None
        raw_date = row.get("purchase_date", "")
        if raw_date:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
                try:
                    purchase_date = dt.strptime(raw_date, fmt)
                    break
                except ValueError:
                    pass

        inv = Investment(
            user_id=current_user.id,
            item_id=item.id,
            purchase_price=purchase_price,
            quantity=quantity,
            purchase_date=purchase_date,
            notes=row.get("notes", "") or None,
            status="active",
            import_source="csv",
        )
        db.add(inv)
        created.append({"row": i, "name": name})

    db.commit()
    return {
        "imported": len(created),
        "errors": errors,
        "items": created,
    }


@router.get("/csv/template")
def download_csv_template():
    """Download a CSV template for import."""
    header = "market_hash_name,purchase_price,quantity,purchase_date,notes\n"
    example = 'AK-47 | Redline (Field-Tested),12.50,2,2024-01-15,Bought the dip\n'
    example2 = 'AWP | Asiimov (Field-Tested),45.00,1,2024-03-01,\n'
    content = header + example + example2

    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=floatbase_import_template.csv"}
    )
