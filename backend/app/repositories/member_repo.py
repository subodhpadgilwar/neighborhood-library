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
    @staticmethod
    def _select_members() -> Select[tuple[Member]]:
        return select(Member).options(*_MEMBER_LOAD_OPTIONS)

    @staticmethod
    def _apply_active_filter(
        stmt: Select[tuple[Member]],
        include_inactive: bool,
    ) -> Select[tuple[Member]]:
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
        library_api.debug("MemberRepository.get_by_email email=%s", email)
        result = await db.execute(select(Member).where(Member.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: MemberCreate) -> Member:
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
        library_api.debug("MemberRepository.soft_delete member_id=%s", member.id)
        member.is_active = False
        member.updated_by = staff_id
        member.updated_at = now_utc()
        await db.commit()
        loaded = await MemberRepository.get_by_id(db, member.id, include_inactive=True)
        return loaded if loaded is not None else member

    @staticmethod
    async def restore(db: AsyncSession, member: Member, staff_id: UUID) -> Member:
        library_api.debug("MemberRepository.restore member_id=%s", member.id)
        member.is_active = True
        member.updated_by = staff_id
        member.updated_at = now_utc()
        await db.commit()
        loaded = await MemberRepository.get_by_id(db, member.id, include_inactive=True)
        return loaded if loaded is not None else member
