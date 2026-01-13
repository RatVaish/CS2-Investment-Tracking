from fastapi import APIRouter
from app.api.v1.endpoints import investments, prices, auth, users, portfolio

api_router = APIRouter()

# Authentication routes (public - no auth required)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# User routes (requires authentication)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

# Investment routes (requires authentication)
api_router.include_router(
    investments.router,
    prefix="/investments",
    tags=["investments"]
)

# Price routes (requires authentication)
api_router.include_router(
    prices.router,
    prefix="/prices",
    tags=["prices"]
)

# Portfolio routes (requires authentication)
api_router.include_router(
    portfolio.router,
    prefix="/portfolio",
    tags=["portfolio"]
)
