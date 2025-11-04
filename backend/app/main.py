from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.scheduler import start_scheduler

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Runs on application startup"""
    start_scheduler()
    print("Application successfully started")

@app.get("/")
def root():
    """
    Root endpoint - Health check
    :return: (dict) Welcome message
    """
    return {"message": "CS2 Investment Tracker API", "status": "running"}
