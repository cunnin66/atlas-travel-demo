from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# Create engine as a module-level singleton
engine = create_engine(
    settings.DATABASE_URL,
    # Connection pool settings for better performance
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections after 5 minutes
)

# Create sessionmaker as a module-level singleton
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Database dependency that yields a database session.
    
    This function creates a new database session for each request,
    ensures it's properly closed after the request is complete,
    and handles any exceptions that might occur.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
