"""Repository layer for member database operations. Contains only database queries — no business logic. All business rules belong in the service layer."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from app.core.logger import library_api
from app.core.timezone import now_utc
from app.models.member import Member
from app.schemas.member import MemberCreate, MemberUpdate

_MEMBER_LOAD_OPTIONS = (
    selectinload(Member.created_by_staff),
    selectinload(Member.updated_by_staff),
)


class MemberRepository:
    """Data access layer for Member entities."""

    @staticmethod
    def _select_members() -> Select[tuple[Member]]:
        """Build a base SELECT for members with staff relationships eager-loaded.

        Returns:
            SQLAlchemy select statement with selectinload options applied.
        """
        return select(Member).options(*_MEMBER_LOAD_OPTIONS)

    @staticmethod
    def _apply_active_filter(
        stmt: Select[tuple[Member]],
        include_inactive: bool,
    ) -> Select[tuple[Member]]:
        """Restrict a query to active members unless include_inactive is True.

        Args:
            stmt: Existing select statement to filter.
            include_inactive: When False (default), only active members are included.

        Returns:
            The statement, optionally filtered by ``Member.is_active``.
        """
        if not include_inactive:
            stmt = stmt.where(Member.is_active.is_(True))
        return stmt

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[Member]:
        """Fetch a paginated list of members.

        Args:
            db: Async database session.
            skip: Number of rows to skip for pagination.
            limit: Maximum number of rows to return.
            include_inactive: When False (default), soft-deleted members are excluded.

        Returns:
            List of Member ORM instances with staff relationships loaded.
        """
        library_api.debug(
            "MemberRepository.get_all skip=%s limit=%s include_inactive=%s",
            skip,
            limit,
            include_inactive,
        )
        stmt = MemberRepository._apply_active_filter(
            MemberRepository._select_members(),
            include_inactive,
        )
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        member_id: UUID,
        include_inactive: bool = False,
    ) -> Member | None:
        """Fetch a single member by primary key.

        Args:
            db: Async database session.
            member_id: Member UUID.
            include_inactive: When False (default), soft-deleted members are excluded.

        Returns:
            The matching Member, or None if not found.
        """
        library_api.debug(
            "MemberRepository.get_by_id member_id=%s include_inactive=%s",
            member_id,
            include_inactive,
        )
        stmt = MemberRepository._apply_active_filter(
            MemberRepository._select_members().where(Member.id == member_id),
            include_inactive,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Member | None:
        """Fetch a member by email without active/inactive filtering.

        Args:
            db: Async database session.
            email: Member email address.

        Returns:
            The matching Member, or None if not found.
        """
        library_api.debug("MemberRepository.get_by_email email=%s", email)
        result = await db.execute(select(Member).where(Member.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: MemberCreate) -> Member:
        """Insert a new member and reload it with relationships.

        Args:
            db: Async database session.
            data: Validated member creation payload.

        Returns:
            The persisted Member with staff relationships loaded.
        """
        library_api.debug("MemberRepository.create email=%s", data.email)
        payload = data.model_dump()
        payload["email"] = str(payload["email"])
        member = Member(**payload)
        db.add(member)
        await db.commit()
        loaded = await MemberRepository.get_by_id(db, member.id, include_inactive=True)
        return loaded if loaded is not None else member

    @staticmethod
    async def update(db: AsyncSession, member: Member, data: MemberUpdate) -> Member:
        """Apply partial field updates to an existing member.

        Args:
            db: Async database session.
            member: Existing Member ORM instance to update.
            data: Validated update payload; None fields are skipped.

        Returns:
            The updated Member with staff relationships loaded.
        """
        library_api.debug("MemberRepository.update member_id=%s", member.id)
        updates = data.model_dump(exclude_none=True)
        if "email" in updates and updates["email"] is not None:
            updates["email"] = str(updates["email"])
        for field, value in updates.items():
            setattr(member, field, value)
        await db.commit()
        loaded = await MemberRepository.get_by_id(db, member.id, include_inactive=True)
        return loaded if loaded is not None else member

    @staticmethod
    async def soft_delete(db: AsyncSession, member: Member, staff_id: UUID) -> Member:
        """Mark a member inactive and record the updating staff member.

        Args:
            db: Async database session.
            member: Member ORM instance to soft-delete.
            staff_id: UUID of the staff member performing the action.

        Returns:
            The updated Member with staff relationships loaded.
        """
        library_api.debug("MemberRepository.soft_delete member_id=%s", member.id)
        member.is_active = False
        member.updated_by = staff_id
        member.updated_at = now_utc()
        await db.commit()
        loaded = await MemberRepository.get_by_id(db, member.id, include_inactive=True)
        return loaded if loaded is not None else member

    @staticmethod
    async def restore(db: AsyncSession, member: Member, staff_id: UUID) -> Member:
        """Reactivate a soft-deleted member.

        Args:
            db: Async database session.
            member: Inactive Member ORM instance to restore.
            staff_id: UUID of the staff member performing the action.

        Returns:
            The updated Member with staff relationships loaded.
        """
        library_api.debug("MemberRepository.restore member_id=%s", member.id)
        member.is_active = True
        member.updated_by = staff_id
        member.updated_at = now_utc()
        await db.commit()
        loaded = await MemberRepository.get_by_id(db, member.id, include_inactive=True)
        return loaded if loaded is not None else member
