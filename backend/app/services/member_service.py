from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateEmailException, MemberNotFoundException
from app.core.logger import library_api
from app.models.member import Member
from app.repositories.lending_repo import LendingRepository
from app.repositories.member_repo import MemberRepository
from app.schemas.member import MemberCreate, MemberUpdate


class MemberService:
    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[Member]:
        return await MemberRepository.get_all(
            db,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
        )

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        member_id: UUID,
        include_inactive: bool = False,
    ) -> Member:
        member = await MemberRepository.get_by_id(
            db,
            member_id,
            include_inactive=include_inactive,
        )
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
        loaded = await MemberRepository.get_by_id(db, member.id, include_inactive=True)
        member = loaded if loaded is not None else member
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

    @staticmethod
    async def soft_delete(db: AsyncSession, member_id: UUID, staff_id: UUID) -> Member:
        member = await MemberRepository.get_by_id(db, member_id, include_inactive=False)
        if member is None:
            raise MemberNotFoundException(member_id)

        active_loans = await LendingRepository.get_active_by_member(db, member_id)
        if active_loans:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete member with {len(active_loans)} active loan(s)",
            )

        member = await MemberRepository.soft_delete(db, member, staff_id)
        library_api.info("Member soft deleted: %s", member_id)
        return member

    @staticmethod
    async def restore(db: AsyncSession, member_id: UUID, staff_id: UUID) -> Member:
        member = await MemberRepository.get_by_id(db, member_id, include_inactive=True)
        if member is None:
            raise MemberNotFoundException(member_id)

        member = await MemberRepository.restore(db, member, staff_id)
        library_api.info("Member restored: %s", member_id)
        return member
