from uuid import UUID

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

        lending = await LendingRepository.create_loan(db, book_id, member_id, staff_id)
        await BookRepository.decrement_copies(db, book)
        library_api.info("Book borrowed: %s by member %s", book_id, member_id)
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
    async def get_member_loans(
        db: AsyncSession,
        member_id: UUID,
    ) -> list[LendingRecord]:
        await MemberService.get_by_id(db, member_id)
        return await LendingRepository.get_by_member(db, member_id)

    @staticmethod
    async def get_all_active(db: AsyncSession) -> list[LendingRecord]:
        return await LendingRepository.get_all_active(db)

    @staticmethod
    async def get_overdue(db: AsyncSession) -> list[LendingRecord]:
        return await LendingRepository.get_overdue(db)
