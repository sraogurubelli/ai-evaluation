"""Database session management."""

import os
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine = None
_session_factory = None


def get_database_url() -> str:
    """
    Get database URL from environment variables.
    
    Returns:
        Database URL string
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Build from individual components
    user = os.getenv("POSTGRES_USER", "aieval")
    password = os.getenv("POSTGRES_PASSWORD", "aieval_dev")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "aieval")
    
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        database_url = get_database_url()
        _engine = create_async_engine(
            database_url,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            future=True,
        )
        logger.info(f"Database engine created for: {database_url.split('@')[1] if '@' in database_url else database_url}")
    return _engine


def get_session_factory():
    """Get or create session factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.
    
    Yields:
        AsyncSession instance
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database (create tables).
    
    This should be called on application startup.
    Note: For production, use Alembic migrations instead.
    """
    engine = get_engine()
    from aieval.db.models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized")


async def close_db() -> None:
    """Close database connections."""
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database connections closed")
