from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

class Settings(BaseSettings):
    DATABASE_URL: str
    PROJECT_NAME: str = "CS Investment Tracker"
    DEBUG: bool = True
    SECRET_KEY: str

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Steam Integration (optional - can be added later)
    STEAM_API_KEY: str = ""
    STEAM_OPENID_REALM: str = "http://localhost:5173"
    STEAM_OPENID_RETURN_URL: str = "http://localhost:8000/api/v1/auth/steam/callback"

    class Config:
        case_sensitive = False

settings = Settings()
