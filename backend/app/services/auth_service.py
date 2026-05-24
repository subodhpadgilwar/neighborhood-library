from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import library_api
from app.core.security import verify_password
from app.models.staff import Staff


async def get_staff_by_email(db: AsyncSession, email: str) -> Staff | None:
    """Look up a staff member by email address."""
    result = await db.execute(select(Staff).where(Staff.email == email))
    return result.scalar_one_or_none()


async def authenticate_staff(
    db: AsyncSession,
    email: str,
    password: str,
) -> Staff | None:
    """Authenticate staff credentials. Returns Staff if valid, otherwise None."""
    staff = await get_staff_by_email(db, email)
    if staff is None or not verify_password(password, staff.hashed_password):
        library_api.warning("Failed login attempt for: %s", email)
        return None

    library_api.info("Staff login: %s", email)
    return staff
