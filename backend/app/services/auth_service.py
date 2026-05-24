"""Service layer for authentication business logic.

Orchestrates between repository layer and API layer. All business rules and
validation that requires database context live here.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import library_api
from app.core.security import verify_password
from app.models.staff import Staff


async def get_staff_by_email(db: AsyncSession, email: str) -> Staff | None:
    """Look up a staff member by email address.

    Args:
        db: Async database session.
        email: Staff email to search for.

    Returns:
        The matching Staff row, or None if not found.
    """
    result = await db.execute(select(Staff).where(Staff.email == email))
    return result.scalar_one_or_none()


async def authenticate_staff(
    db: AsyncSession,
    email: str,
    password: str,
) -> Staff | None:
    """Authenticate staff credentials against the database.

    Args:
        db: Async database session.
        email: Staff email submitted at login.
        password: Plain-text password to verify.

    Returns:
        The authenticated Staff if credentials are valid and the account is
        active; otherwise None (failed attempts are logged).
    """
    staff = await get_staff_by_email(db, email)
    if (
        staff is None
        or not staff.is_active
        or not verify_password(password, staff.hashed_password)
    ):
        library_api.warning("Failed login attempt for: %s", email)
        return None

    library_api.info("Staff login: %s", email)
    return staff
