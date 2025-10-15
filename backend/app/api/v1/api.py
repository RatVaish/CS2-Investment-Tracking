from fastapi import APIRouter
from app.api.v1.endpoints import investments

api_router = APIRouter()

api_router.include_router(
    investments.router,
    prefix="/investments",
    tags=["investments"]
)
