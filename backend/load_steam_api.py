from app.services.steam_market import steam_market_api

item_name = "AK-47 | Redline (Field-Tested)"
print(f"Testing Steam Market API for {item_name}")

result = steam_market_api.get_item_price(item_name)

if result:
    print(f"✓ Success!")
    print(f"  Price: ${result['price']:.2f}")
    print(f"  Volume: {result['volume']}")
    print(f"  Timestamp: {result['timestamp']}")
else:
    print("✗ Failed to fetch price")

sticker_name = "Sticker | Katowice 2014"
print(f"\nTesting with: {sticker_name}")

result2 = steam_market_api.get_item_price(sticker_name)

if result2:
    print(f"✓ Success!")
    print(f"  Price: ${result2['price']:.2f}")
else:
    print("✗ Failed to fetch price (may not exist on Steam Market)")
