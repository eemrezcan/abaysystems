# app/db/session.py
from sqlalchemy import create_engine
from typing import Generator
from sqlalchemy.orm import sessionmaker, Session

from app.core.settings import settings

engine = create_engine(settings.database_url, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: request başına tek bir DB oturumu açar, iş bitince kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()