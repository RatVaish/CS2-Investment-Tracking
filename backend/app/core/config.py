import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "CS2 Investment Tracker"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "Track your Counter-Strike 2 item investments with real-time pricing"

    DEBUG: bool = os.getenv("DEBUG", "False") == "True"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/cs_investments")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:5173"]


settings = Settings()