from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, investments, prices, portfolio, items

api_router = APIRouter()

# Public routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# Protected routes
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    items.router,
    prefix="/items",
    tags=["items"]
)

api_router.include_router(
    investments.router,
    prefix="/investments",
    tags=["investments"]
)

api_router.include_router(
    prices.router,
    prefix="/prices",
    tags=["prices"]
)

api_router.include_router(
    portfolio.router,
    prefix="/portfolio",
    tags=["portfolio"]
)