from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.scheduler import start_scheduler, stop_scheduler
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Startup event - Start scheduler
@app.on_event("startup")
async def startup_event():
    logger.info(f"✅ {settings.PROJECT_NAME} v{settings.VERSION} started")
    start_scheduler()

# Shutdown event - Stop scheduler
@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"👋 {settings.PROJECT_NAME} shutting down")
    stop_scheduler()

@app.get("/")
def root():
    """Root endpoint - Health check"""
    return {
        "message": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}
