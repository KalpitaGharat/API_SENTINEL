"""Database engine and session management using SQLAlchemy."""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

# SQLite-specific connection arguments with 30-second busy timeout
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
        "timeout": 30.0,
    }

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG and settings.ENVIRONMENT == "development",
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configure SQLite PRAGMAs for concurrency, foreign keys, and WAL durability."""
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA busy_timeout=30000;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            # Enable Write-Ahead Logging (WAL) for persistent file-based databases
            if ":memory:" not in settings.DATABASE_URL:
                cursor.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
        finally:
            cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency for yielding database sessions."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
