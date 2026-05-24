from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateEmailException, MemberNotFoundException
from app.core.logger import library_api
from app.models.member import Member
from app.repositories.member_repo import MemberRepository
from app.schemas.member import MemberCreate, MemberUpdate


class MemberService:
    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Member]:
        return await MemberRepository.get_all(db, skip=skip, limit=limit)

    @staticmethod
    async def get_by_id(db: AsyncSession, member_id: UUID) -> Member:
        member = await MemberRepository.get_by_id(db, member_id)
        if member is None:
            raise MemberNotFoundException(member_id)
        return member

    @staticmethod
    async def create(db: AsyncSession, data: MemberCreate, staff_id: UUID) -> Member:
        email = str(data.email)
        existing = await MemberRepository.get_by_email(db, email)
        if existing is not None:
            raise DuplicateEmailException(email)

        member = await MemberRepository.create(db, data)
        member.created_by = staff_id
        await db.commit()
        await db.refresh(member)
        library_api.info("Member registered: %s", member.email)
        return member

    @staticmethod
    async def update(
        db: AsyncSession,
        member_id: UUID,
        data: MemberUpdate,
        staff_id: UUID,
    ) -> Member:
        member = await MemberRepository.get_by_id(db, member_id)
        if member is None:
            raise MemberNotFoundException(member_id)

        if data.email is not None:
            new_email = str(data.email)
            if new_email != member.email:
                existing = await MemberRepository.get_by_email(db, new_email)
                if existing is not None:
                    raise DuplicateEmailException(new_email)

        member.updated_by = staff_id
        return await MemberRepository.update(db, member, data)
