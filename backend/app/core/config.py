import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Floatbase"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "The home base for CS2 float data and investment tracking"
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
    @property
    def ALLOWED_ORIGINS(self) -> list:
        origins_env = os.getenv("ALLOWED_ORIGINS", "")
        if origins_env:
            return [o.strip() for o in origins_env.split(",") if o.strip()]
        return [
            "http://localhost:5173",
            "http://localhost:80",
            "http://localhost",
            "https://floatbase.app",
        ]

    # CSFloat API
    CSFLOAT_API_KEY: str = os.getenv("CSFLOAT_API_KEY", "")

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")

    # Steam
    STEAM_API_KEY: str = os.getenv("STEAM_API_KEY", "")
    STEAM_RETURN_URL: str = os.getenv("STEAM_RETURN_URL", "http://localhost:8000/api/v1/auth/steam/callback")
    STEAM_LOGIN_SECURE: str = os.getenv("STEAM_LOGIN_SECURE", "")
    STEAM_SESSION_ID: str = os.getenv("STEAM_SESSION_ID", "")

    # Buff163
    BUFF_SESSION_COOKIE: str = os.getenv("BUFF_SESSION_COOKIE", "")

    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_MONTHLY_PRICE_ID: str = os.getenv("STRIPE_MONTHLY_PRICE_ID", "")
    STRIPE_ANNUAL_PRICE_ID: str = os.getenv("STRIPE_ANNUAL_PRICE_ID", "")

    # Telegram notifications
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Resend email
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")


settings = Settings()
