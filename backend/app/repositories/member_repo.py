from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import library_api
from app.models.member import Member
from app.schemas.member import MemberCreate, MemberUpdate


class MemberRepository:
    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Member]:
        library_api.debug("MemberRepository.get_all skip=%s limit=%s", skip, limit)
        result = await db.execute(select(Member).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, member_id: UUID) -> Member | None:
        library_api.debug("MemberRepository.get_by_id member_id=%s", member_id)
        result = await db.execute(select(Member).where(Member.id == member_id))
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
        await db.refresh(member)
        return member

    @staticmethod
    async def update(db: AsyncSession, member: Member, data: MemberUpdate) -> Member:
        library_api.debug("MemberRepository.update member_id=%s", member.id)
        updates = data.model_dump(exclude_none=True)
        if "email" in updates and updates["email"] is not None:
            updates["email"] = str(updates["email"])
        for field, value in updates.items():
            setattr(member, field, value)
        await db.commit()
        await db.refresh(member)
        return member
