from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyBorrowedException,
    AlreadyReturnedException,
    BookNotAvailableException,
    BookNotFoundException,
    LendingNotFoundException,
    MemberNotFoundException,
)
from app.core.logger import library_api
from app.core.timezone import now_utc, to_local, to_utc
from app.models.lending import LendingRecord
from app.repositories.book_repo import BookRepository
from app.repositories.lending_repo import LendingRepository
from app.repositories.member_repo import MemberRepository
from app.services.member_service import MemberService


class LendingService:
    @staticmethod
    async def borrow_book(
        db: AsyncSession,
        book_id: UUID,
        member_id: UUID,
        staff_id: UUID,
        due_date: datetime | None = None,
    ) -> LendingRecord:
        book = await BookRepository.get_by_id(db, book_id)
        if book is None:
            raise BookNotFoundException(book_id)

        member = await MemberRepository.get_by_id(db, member_id)
        if member is None:
            raise MemberNotFoundException(member_id)

        if book.copies_available <= 0:
            raise BookNotAvailableException()

        active_loan = await LendingRepository.get_active_loan(db, book_id, member_id)
        if active_loan is not None:
            raise AlreadyBorrowedException()

        if due_date is None:
            calculated_due = now_utc() + timedelta(days=14)
        else:
            if to_utc(due_date) <= now_utc():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Due date must be after current date and time",
                )
            calculated_due = to_utc(due_date)
            if calculated_due is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Due date must be after current date and time",
                )

        lending = await LendingRepository.create_loan(
            db,
            book_id,
            member_id,
            staff_id,
            calculated_due,
        )
        await BookRepository.decrement_copies(db, book)
        library_api.info(
            "Book borrowed: book=%s member=%s due=%s",
            book_id,
            member_id,
            calculated_due,
        )
        return lending

    @staticmethod
    async def return_book(
        db: AsyncSession,
        lending_id: UUID,
        staff_id: UUID,
    ) -> LendingRecord:
        lending = await LendingRepository.get_by_id(db, lending_id)
        if lending is None:
            raise LendingNotFoundException()

        if lending.returned_at is not None:
            raise AlreadyReturnedException()

        lending = await LendingRepository.mark_returned(db, lending, staff_id)

        book = await BookRepository.get_by_id(db, lending.book_id)
        if book is not None:
            await BookRepository.increment_copies(db, book)

        library_api.info("Book returned: lending %s", lending_id)
        return lending

    @staticmethod
    async def update_due_date(
        db: AsyncSession,
        lending_id: UUID,
        due_date: datetime,
        staff_id: UUID,
    ) -> LendingRecord:
        lending = await LendingRepository.get_by_id(db, lending_id)
        if lending is None:
            raise LendingNotFoundException()

        if lending.returned_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update due date of returned book",
            )

        utc_due_date = to_utc(due_date)
        if utc_due_date is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date cannot be set in the past",
            )

        if utc_due_date < lending.borrowed_at:
            borrowed_local = to_local(lending.borrowed_at)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Due date cannot be before borrow date ({borrowed_local})",
            )

        lending = await LendingRepository.update_due_date(
            db,
            lending,
            utc_due_date,
            staff_id,
        )
        library_api.info(
            "Due date updated: lending=%s new_due=%s by staff=%s",
            lending_id,
            utc_due_date,
            staff_id,
        )
        return lending

    @staticmethod
    async def get_member_loans(
        db: AsyncSession,
        member_id: UUID,
    ) -> list[LendingRecord]:
        await MemberService.get_by_id(db, member_id)
        return await LendingRepository.get_by_member(db, member_id)

    @staticmethod
    async def get_member_active_loans(
        db: AsyncSession,
        member_id: UUID,
    ) -> list[LendingRecord]:
        await MemberService.get_by_id(db, member_id)
        return await LendingRepository.get_active_by_member(db, member_id)

    @staticmethod
    async def get_all_active(db: AsyncSession) -> list[LendingRecord]:
        return await LendingRepository.get_all_active(db)

    @staticmethod
    async def get_overdue(db: AsyncSession) -> list[LendingRecord]:
        return await LendingRepository.get_overdue(db)
