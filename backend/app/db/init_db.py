"""Database initialization script to create tables and execute seeding."""

import logging
from app.db.base import Base
from app.db.session import engine, SessionLocal
import app.models  # noqa: F401 - ensure all models are registered with Base.metadata
from app.db.seed import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create all relational tables and run seed data."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created or already exist.")

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
