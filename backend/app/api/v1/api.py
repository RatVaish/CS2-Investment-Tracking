from fastapi import APIRouter
from app.api.v1.endpoints.investments import router as investments_router
from app.api.v1.endpoints.prices import router as prices_router
from app.api.v1.endpoints.price_history import router as price_history_router
from app.api.v1.endpoints.portfolio import router as portfolio_router

api_router = APIRouter()

api_router.include_router(
    investments_router,
    prefix="/investments",
    tags=["investments"]
)

api_router.include_router(
    prices_router,
    prefix="/prices",
    tags=["prices"]
)

api_router.include_router(
    price_history_router,
    prefix="/price_history",
    tags=["price_history"]
)

api_router.include_router(
    portfolio_router,
    prefix="/portfolio",
    tags=["portfolio"]
)
