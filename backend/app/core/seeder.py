from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logger import library_api
from app.core.security import hash_password
from app.models.staff import Staff
from app.services.auth_service import get_staff_by_email


async def seed_default_admin(db: AsyncSession) -> None:
    """
    Ensure the default admin staff account exists.

    Idempotent and safe to run on every application startup.
    Errors are logged and swallowed so startup is not blocked.
    """
    try:
        admin_email = str(settings.admin_email)
        existing = await get_staff_by_email(db, admin_email)
        if existing is not None:
            library_api.info("Default admin exists, skipping")
            return

        staff = Staff(
            email=admin_email,
            hashed_password=hash_password(settings.admin_password),
            full_name=settings.admin_full_name,
            is_default_admin=True,
        )
        db.add(staff)
        await db.commit()
        library_api.info("Default admin created: %s", admin_email)
    except Exception as exc:
        library_api.error("Failed to seed default admin: %s", exc, exc_info=True)
        await db.rollback()
