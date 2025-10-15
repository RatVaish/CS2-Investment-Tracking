from typing import Generator
from app.db.session import SessionLocal

def get_db() -> Generator:
    """
    Dependency that creates a new database session for each request.
    Yields the session, closing it after the request is finished.
    :return: (Generator) Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
