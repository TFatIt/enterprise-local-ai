"""Database connection engine and session management with high-concurrency SQLite WAL & PostgreSQL support."""

import logging
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

from sqlalchemy.pool import NullPool

db_url = settings.DATABASE_URL
connect_args = {}
engine_kwargs = {"echo": False}

if db_url.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
        "timeout": 15,
    }
    engine_kwargs["poolclass"] = NullPool
else:
    connect_args = {"connect_timeout": 2}
    engine_kwargs["pool_pre_ping"] = True

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        **engine_kwargs
    )
    with engine.connect() as conn:
        pass
except Exception as e:
    logger.warning(
        f"Could not connect to database at {db_url}. "
        "Falling back to local SQLite database: sqlite:///./enterprise_local_dev.db"
    )
    db_url = "sqlite:///./enterprise_local_dev.db"
    connect_args = {"check_same_thread": False, "timeout": 15}
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        poolclass=NullPool,
        echo=False,
    )

if db_url.startswith("sqlite"):
    # Enable WAL mode once on engine initialization
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
    except Exception:
        pass

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA busy_timeout=15000;")
            cursor.close()
        except Exception:
            pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to yield a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
