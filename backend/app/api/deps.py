from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenException
from app.core.logger import library_api
from app.core.security import decode_access_token
from app.database import AsyncSessionLocal
from app.models.staff import Staff

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for the duration of a request."""
    session = AsyncSessionLocal()
    try:
        yield session
    except SQLAlchemyError as exc:
        library_api.error("Database connection error: %s", exc, exc_info=True)
        raise
    finally:
        await session.close()


async def get_current_staff(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> Staff:
    """Resolve the authenticated staff member from a Bearer JWT."""
    payload = decode_access_token(token)
    if payload is None:
        raise InvalidTokenException()

    staff_id_raw = payload.get("sub")
    if staff_id_raw is None:
        raise InvalidTokenException()

    try:
        staff_id = UUID(str(staff_id_raw))
    except (TypeError, ValueError):
        raise InvalidTokenException()

    result = await db.execute(select(Staff).where(Staff.id == staff_id))
    staff = result.scalar_one_or_none()
    if staff is None:
        raise InvalidTokenException()

    return staff
