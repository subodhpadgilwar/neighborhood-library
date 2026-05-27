"""Repository layer for staff database operations. Contains only database queries — no business logic. All business rules belong in the service layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.core.logger import library_api
from app.core.security import hash_password
from app.core.timezone import now_utc
from app.models.staff import Staff
from app.schemas.staff import StaffCreate, StaffUpdate


class StaffRepository:
    """Data access layer for Staff entities."""

    @staticmethod
    def _select_staff() -> Select[tuple[Staff]]:
        """Build a base SELECT for staff records.

        Returns:
            SQLAlchemy select statement for Staff.
        """
        return select(Staff)

    @staticmethod
    def _apply_active_filter(
        stmt: Select[tuple[Staff]],
        include_inactive: bool,
    ) -> Select[tuple[Staff]]:
        """Restrict a query to active staff unless include_inactive is True.

        Args:
            stmt: Existing select statement to filter.
            include_inactive: When False (default), only active staff are included.

        Returns:
            The statement, optionally filtered by ``Staff.is_active``.
        """
        if not include_inactive:
            stmt = stmt.where(Staff.is_active.is_(True))
        return stmt

    @staticmethod
    def _apply_sort(
        stmt: Select[tuple[Staff]],
        sort_by: str,
        sort_order: str,
    ) -> Select[tuple[Staff]]:
        """Apply a safe sort expression for staff lists."""
        columns = {
            "full_name": Staff.full_name,
            "email": Staff.email,
            "created_at": Staff.created_at,
        }
        sort_column = columns.get(sort_by, Staff.full_name)
        if sort_order == "desc":
            return stmt.order_by(sort_column.desc())
        return stmt.order_by(sort_column.asc())

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        sort_by: str = "full_name",
        sort_order: str = "asc",
    ) -> list[Staff]:
        """Fetch a paginated list of staff records.

        Args:
            db: Async database session.
            skip: Number of rows to skip for pagination.
            limit: Maximum number of rows to return.
            include_inactive: When False (default), deactivated staff are excluded.
            sort_by: Column key to sort by.
            sort_order: ``asc`` or ``desc``.

        Returns:
            List of Staff ORM instances.
        """
        library_api.debug(
            "StaffRepository.get_all skip=%s limit=%s include_inactive=%s",
            skip,
            limit,
            include_inactive,
        )
        stmt = StaffRepository._apply_active_filter(
            StaffRepository._select_staff(),
            include_inactive,
        )
        stmt = StaffRepository._apply_sort(stmt, sort_by, sort_order)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def count(
        db: AsyncSession,
        include_inactive: bool = False,
    ) -> int:
        """Count staff matching the same filters used by ``get_all``."""
        stmt = StaffRepository._apply_active_filter(select(Staff), include_inactive).subquery()
        result = await db.execute(select(func.count()).select_from(stmt))
        return int(result.scalar_one())

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        staff_id: UUID,
        include_inactive: bool = False,
    ) -> Staff | None:
        """Fetch a single staff member by primary key.

        Args:
            db: Async database session.
            staff_id: Staff UUID.
            include_inactive: When False (default), deactivated staff are excluded.

        Returns:
            The matching Staff, or None if not found.
        """
        library_api.debug(
            "StaffRepository.get_by_id staff_id=%s include_inactive=%s",
            staff_id,
            include_inactive,
        )
        stmt = StaffRepository._apply_active_filter(
            StaffRepository._select_staff().where(Staff.id == staff_id),
            include_inactive,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Staff | None:
        """Fetch a staff member by email without active/inactive filtering.

        Args:
            db: Async database session.
            email: Staff email address.

        Returns:
            The matching Staff, or None if not found.
        """
        library_api.debug("StaffRepository.get_by_email email=%s", email)
        result = await db.execute(
            StaffRepository._select_staff().where(Staff.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: StaffCreate) -> Staff:
        """Insert a new staff account with a hashed password.

        Args:
            db: Async database session.
            data: Validated staff creation payload including plain-text password.

        Returns:
            The persisted Staff ORM instance.
        """
        library_api.debug("StaffRepository.create email=%s", data.email)
        staff = Staff(
            email=str(data.email),
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role,
        )
        db.add(staff)
        await db.flush()
        return staff

    @staticmethod
    async def update(db: AsyncSession, staff: Staff, data: StaffUpdate) -> Staff:
        """Apply partial profile updates to an existing staff member.

        Args:
            db: Async database session.
            staff: Existing Staff ORM instance to update.
            data: Validated update payload; None fields are skipped.

        Returns:
            The updated Staff ORM instance.
        """
        library_api.debug("StaffRepository.update staff_id=%s", staff.id)
        updates = data.model_dump(exclude_none=True)
        if "email" in updates and updates["email"] is not None:
            updates["email"] = str(updates["email"])
        for field, value in updates.items():
            setattr(staff, field, value)
        staff.updated_at = now_utc()
        await db.flush()
        return staff

    @staticmethod
    async def update_password(db: AsyncSession, staff: Staff, new_password: str) -> Staff:
        """Replace a staff member's hashed password.

        Args:
            db: Async database session.
            staff: Staff ORM instance whose password will change.
            new_password: Plain-text new password to hash and store.

        Returns:
            The updated Staff ORM instance.
        """
        library_api.debug("StaffRepository.update_password staff_id=%s", staff.id)
        staff.hashed_password = hash_password(new_password)
        staff.updated_at = now_utc()
        await db.flush()
        return staff

    @staticmethod
    async def soft_delete(db: AsyncSession, staff: Staff) -> Staff:
        """Mark a staff account inactive.

        Args:
            db: Async database session.
            staff: Staff ORM instance to deactivate.

        Returns:
            The updated Staff ORM instance.
        """
        library_api.debug("StaffRepository.soft_delete staff_id=%s", staff.id)
        staff.is_active = False
        staff.updated_at = now_utc()
        await db.flush()
        return staff

    @staticmethod
    async def restore(db: AsyncSession, staff: Staff) -> Staff:
        """Reactivate a deactivated staff account.

        Args:
            db: Async database session.
            staff: Inactive Staff ORM instance to restore.

        Returns:
            The updated Staff ORM instance.
        """
        library_api.debug("StaffRepository.restore staff_id=%s", staff.id)
        staff.is_active = True
        staff.updated_at = now_utc()
        await db.flush()
        return staff
