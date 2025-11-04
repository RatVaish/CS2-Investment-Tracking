from app.db.session import SessionLocal
from app.models.investment import Investment

print("Creating database session...")
db = SessionLocal()
print("✓ Database session created!")

print("Querying investments...")
investments = db.query(Investment).all()
print(f"✓ Found {len(investments)} investments")

for inv in investments[:3]:
    print(f"  - {inv.item_name}")

db.close()
print("✓ Done!")