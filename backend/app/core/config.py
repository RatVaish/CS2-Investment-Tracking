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

    class Config:
        case_sensitive = False

settings = Settings()
