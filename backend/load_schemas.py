from app.schemas.investment import InvestmentCreate
from app.models.investment import ItemType

# Test creating a schema
data = {
    "item_name": "Sticker | Katowice 2014 Titan (Holo)",
    "item_type": ItemType.STICKER,
    "purchase_price": 85000.00,
    "quantity": 1
}

investment = InvestmentCreate(**data)
print("✓ Schema created successfully!")
print(f"Item: {investment.item_name}")
print(f"Type: {investment.item_type}")
print(f"Price: ${investment.purchase_price:,.2f}")