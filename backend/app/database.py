"""Async PostgreSQL database configuration using SQLAlchemy.

Provides the async engine, session factory, declarative ``Base``, and the
``get_db`` FastAPI dependency used by route handlers and services.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.core.logger import library_api


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy ORM models."""


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for the request lifecycle.

    The session is always closed in ``finally``, including when errors occur.

    Yields:
        AsyncSession: Per-request database session.

    Raises:
        SQLAlchemyError: Logged and re-raised on connection failures.
    """
    session = AsyncSessionLocal()
    try:
        yield session
    except SQLAlchemyError as exc:
        library_api.error("Database connection error: %s", exc, exc_info=True)
        raise
    finally:
        await session.close()
