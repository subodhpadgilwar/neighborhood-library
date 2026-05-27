"""Transaction boundary helper for service-layer write operations.

Services own commits; repositories only flush. This module provides a single,
consistent pattern for committing on success and rolling back on failure while
preserving domain exceptions without swallowing them.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainException


@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Commit the session on success; roll back on any error.

    Domain exceptions are re-raised after rollback so API-layer handlers can
    map them to consistent JSON envelopes.

    ``IntegrityError`` is rolled back and re-raised for callers that map unique
    violations to domain exceptions (e.g. duplicate ISBN or active loan).

    Args:
        session: Active async SQLAlchemy session (not auto-committed by ``get_db``).

    Yields:
        The same session for use inside the block.
    """
    try:
        yield session
    except DomainException:
        await session.rollback()
        raise
    except IntegrityError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise
    else:
        await session.commit()
