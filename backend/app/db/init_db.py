"""Database initialization utilities."""

from sqlalchemy import text

from app.core.config import settings
from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import engine

logger = get_logger(__name__)


async def init_db() -> None:
    """Create database tables if they do not exist.

    In production, prefer Alembic migrations over auto-create.
    """
    if settings.ENVIRONMENT == "production":
        logger.info("skipping_auto_create_in_production")
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # SQLite-specific pragma for foreign keys
    if settings.is_sqlite:
        async with engine.begin() as conn:
            await conn.execute(text("PRAGMA foreign_keys=ON"))

    logger.info("database_initialized")
