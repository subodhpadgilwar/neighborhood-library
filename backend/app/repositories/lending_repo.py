from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logger import library_api
from app.core.timezone import now_utc
from app.models.lending import LendingRecord

_LENDING_LOAD_OPTIONS = (
    selectinload(LendingRecord.book),
    selectinload(LendingRecord.member),
    selectinload(LendingRecord.created_by_staff),
)


class LendingRepository:
    @staticmethod
    def _select_lending():
        return select(LendingRecord).options(*_LENDING_LOAD_OPTIONS)

    @staticmethod
    async def get_by_id(db: AsyncSession, lending_id: UUID) -> LendingRecord | None:
        library_api.debug("LendingRepository.get_by_id lending_id=%s", lending_id)
        result = await db.execute(
            LendingRepository._select_lending().where(LendingRecord.id == lending_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_by_book(
        db: AsyncSession,
        book_id: UUID,
    ) -> list[LendingRecord]:
        library_api.debug("LendingRepository.get_active_by_book book_id=%s", book_id)
        result = await db.execute(
            select(LendingRecord).where(
                LendingRecord.book_id == book_id,
                LendingRecord.returned_at.is_(None),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_active_loan(
        db: AsyncSession,
        book_id: UUID,
        member_id: UUID,
    ) -> LendingRecord | None:
        library_api.debug(
            "LendingRepository.get_active_loan book_id=%s member_id=%s",
            book_id,
            member_id,
        )
        result = await db.execute(
            select(LendingRecord).where(
                LendingRecord.book_id == book_id,
                LendingRecord.member_id == member_id,
                LendingRecord.returned_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_member(db: AsyncSession, member_id: UUID) -> list[LendingRecord]:
        library_api.debug("LendingRepository.get_by_member member_id=%s", member_id)
        result = await db.execute(
            LendingRepository._select_lending()
            .where(LendingRecord.member_id == member_id)
            .order_by(LendingRecord.borrowed_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_active_by_member(
        db: AsyncSession,
        member_id: UUID,
    ) -> list[LendingRecord]:
        library_api.debug(
            "LendingRepository.get_active_by_member member_id=%s",
            member_id,
        )
        result = await db.execute(
            LendingRepository._select_lending()
            .where(
                LendingRecord.member_id == member_id,
                LendingRecord.returned_at.is_(None),
            )
            .order_by(LendingRecord.borrowed_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_all_active(db: AsyncSession) -> list[LendingRecord]:
        library_api.debug("LendingRepository.get_all_active")
        result = await db.execute(
            LendingRepository._select_lending().where(
                LendingRecord.returned_at.is_(None)
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_overdue(db: AsyncSession) -> list[LendingRecord]:
        library_api.debug("LendingRepository.get_overdue")
        current_time = now_utc()
        result = await db.execute(
            LendingRepository._select_lending().where(
                LendingRecord.returned_at.is_(None),
                LendingRecord.due_date < current_time,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_loan(
        db: AsyncSession,
        book_id: UUID,
        member_id: UUID,
        staff_id: UUID,
        due_date: datetime,
    ) -> LendingRecord:
        library_api.debug(
            "LendingRepository.create_loan book_id=%s member_id=%s staff_id=%s",
            book_id,
            member_id,
            staff_id,
        )
        borrowed_at = now_utc()
        lending = LendingRecord(
            book_id=book_id,
            member_id=member_id,
            borrowed_at=borrowed_at,
            due_date=due_date,
            created_by=staff_id,
        )
        db.add(lending)
        await db.commit()
        loaded = await LendingRepository.get_by_id(db, lending.id)
        return loaded if loaded is not None else lending

    @staticmethod
    async def update_due_date(
        db: AsyncSession,
        lending: LendingRecord,
        new_due_date: datetime,
        staff_id: UUID,
    ) -> LendingRecord:
        library_api.debug(
            "LendingRepository.update_due_date lending_id=%s staff_id=%s",
            lending.id,
            staff_id,
        )
        lending.due_date = new_due_date
        lending.updated_by = staff_id
        lending.updated_at = now_utc()
        await db.commit()
        loaded = await LendingRepository.get_by_id(db, lending.id)
        return loaded if loaded is not None else lending

    @staticmethod
    async def mark_returned(
        db: AsyncSession,
        lending: LendingRecord,
        staff_id: UUID,
    ) -> LendingRecord:
        library_api.debug(
            "LendingRepository.mark_returned lending_id=%s staff_id=%s",
            lending.id,
            staff_id,
        )
        lending.returned_at = now_utc()
        lending.updated_by = staff_id
        await db.commit()
        loaded = await LendingRepository.get_by_id(db, lending.id)
        return loaded if loaded is not None else lending
