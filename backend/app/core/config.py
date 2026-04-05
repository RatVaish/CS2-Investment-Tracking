import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "CS2 Investment Tracker"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "Track your Counter-Strike 2 item investments with real-time pricing"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/cs_investments")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: list = [
	"http://localhost:5173",
	"http://100.95.133.40",
	"http://100.95.133.40:80",
	"http://192.168.1.232:80",
    ]
    
    # CSFloat API
    CSFLOAT_API_KEY: str = os.getenv("CSFLOAT_API_KEY", "")

    #Buff Session Cookie
    BUFF_SESSION_COOKIE: str = os.getenv("BUFF_SESSION_COOKIE", "")

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")

    # Steam API
    STEAM_API_KEY: str = os.getenv("STEAM_API_KEY", "") 
    STEAM_RETURN_URL: str = os.getenv("STEAM_RETURN_URL", "http://localhost:8000/api/v1/auth/steam/callback") 
    STEAM_LOGIN_SECURE: str = os.getenv("STEAM_LOGIN_SECURE", "")

settings = Settings()
