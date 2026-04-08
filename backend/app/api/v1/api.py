from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, investments, prices, portfolio, items
from app.api.v1.endpoints import google_auth, steam_auth, payments, import_data, health

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(investments.router, prefix="/investments", tags=["investments"])
api_router.include_router(prices.router, prefix="/prices", tags=["prices"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(import_data.router, prefix="/import", tags=["import"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(google_auth.router, prefix="/auth/google", tags=["google-auth"])
api_router.include_router(steam_auth.router, prefix="/auth/steam", tags=["steam-auth"])
