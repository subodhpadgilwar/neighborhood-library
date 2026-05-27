"""FastAPI dependencies for authentication and shared request resources.

Used with ``Depends()`` in route handlers throughout the API to resolve the
current authenticated staff member. The database dependency is re-exported
from ``app.database`` so there is a single request-session implementation.
"""

from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AdminRequiredException, InvalidTokenException
from app.core.security import decode_access_token
from app.database import get_db
from app.models.staff import Staff

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_optional_staff(
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(
        OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
    ),
) -> Staff | None:
    """Resolve the current staff if a valid Bearer token is present, else return None."""
    if token is None:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    staff_id_raw = payload.get("sub")
    if staff_id_raw is None:
        return None
    try:
        staff_id = UUID(str(staff_id_raw))
    except (TypeError, ValueError):
        return None
    result = await db.execute(select(Staff).where(Staff.id == staff_id))
    staff = result.scalar_one_or_none()
    if staff is None or not staff.is_active:
        return None
    return staff


async def get_current_staff(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> Staff:
    """Resolve the authenticated staff member from a Bearer JWT.

    Args:
        db: Async database session from ``get_db``.
        token: OAuth2 bearer access token.

    Returns:
        Active Staff model for the token subject.

    Raises:
        InvalidTokenException: If the token is missing, invalid, expired, or
            refers to an inactive or unknown staff account.
    """
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
    if staff is None or not staff.is_active:
        raise InvalidTokenException()

    return staff


async def require_admin(
    current_staff: Staff = Depends(get_current_staff),
) -> Staff:
    """Require the authenticated staff member to have the admin role."""
    if current_staff.role != "admin":
        raise AdminRequiredException()
    return current_staff
