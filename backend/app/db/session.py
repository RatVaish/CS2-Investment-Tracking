from sqlalchemy import  create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base
import app.models

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping = True,
    echo = settings.DEBUG
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
