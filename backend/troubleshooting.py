from app.main import app
print("✓ App imported successfully!")

# Try to see what the app has
print(f"Routes: {[route.path for route in app.routes]}")
