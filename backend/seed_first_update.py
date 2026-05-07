"""Seed first update: Updates display feature"""
from datetime import datetime
from app.db.session import SessionLocal
from app.models.update import Update


def seed_first_update():
    db = SessionLocal()
    try:
        # Check if update already exists
        existing = db.query(Update).filter(Update.title == "Updates display").first()
        if existing:
            print("First update already exists, skipping.")
            return
        
        # Create the first update
        first_update = Update(
            title="Updates display",
            description="Stay in the loop with new feature announcements! You'll now see a popup when we add new features, so you never miss important updates to Floatbase.",
            image_url=None,  # Can add icon/screenshot URL later
            created_at=datetime.utcnow().isoformat()
        )
        
        db.add(first_update)
        db.commit()
        print(f"✓ Seeded first update (ID: {first_update.id})")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding update: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_first_update()
