"""Service layer for lending business logic.

Orchestrates between repository layer and API layer. All business rules and
validation that requires database context live here.
"""

import math
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
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
from app.schemas.lending import LendingFilterParams, LendingHistoryResponse, LendingResponse
from app.services.member_service import MemberService


class LendingService:
    """Business logic for book borrow, return, and loan queries."""

    @staticmethod
    async def borrow_book(
        db: AsyncSession,
        book_id: UUID,
        member_id: UUID,
        staff_id: UUID,
        due_date: datetime | None = None,
    ) -> LendingRecord:
        """Create a new loan after validating borrow eligibility.

        Enforces rules 1-4 before creating the lending record and decrementing
        available copies:
            1. The book must exist.
            2. The member must exist.
            3. At least one copy must be available.
            4. The member must not already have an active loan for this book.

        When ``due_date`` is omitted, the due date defaults to 14 days from now
        (UTC). A custom due date must be strictly in the future.

        Args:
            db: Async database session.
            book_id: UUID of the book to borrow.
            member_id: UUID of the borrowing member.
            staff_id: UUID of the staff member processing the loan.
            due_date: Optional due datetime (converted to UTC); defaults to
                14 days from borrow time when omitted.

        Returns:
            The newly created LendingRecord.

        Raises:
            BookNotFoundException: Rule 1 — book does not exist.
            MemberNotFoundException: Rule 2 — member does not exist.
            BookNotAvailableException: Rule 3 — no copies available.
            AlreadyBorrowedException: Rule 4 — duplicate active loan for this
                book and member pair.
        """
        if due_date is None:
            calculated_due = now_utc() + timedelta(days=14)
        else:
            utc_due_date = to_utc(due_date)
            if utc_due_date is None or utc_due_date <= now_utc():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Due date must be after current date and time",
                )
            calculated_due = utc_due_date

        try:
            book = await BookRepository.get_by_id_for_update(db, book_id)
            if book is None:
                raise BookNotFoundException(book_id)

            member = await MemberRepository.get_by_id(db, member_id)
            if member is None:
                raise MemberNotFoundException(member_id)

            if book.copies_available <= 0:
                raise BookNotAvailableException()

            active_loan = await LendingRepository.get_active_loan(
                db,
                book_id,
                member_id,
            )
            if active_loan is not None:
                raise AlreadyBorrowedException()

            lending = await LendingRepository.create_loan(
                db,
                book_id,
                member_id,
                staff_id,
                calculated_due,
            )
            await BookRepository.decrement_copies(db, book)
            lending_id = lending.id
            await db.commit()
        except IntegrityError as exc:
            await db.rollback()
            raise AlreadyBorrowedException() from exc
        except Exception:
            await db.rollback()
            raise

        loaded = await LendingRepository.get_by_id(db, lending_id)
        lending = loaded if loaded is not None else lending
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
        """Mark a loan as returned and restore one available copy when possible.

        Args:
            db: Async database session.
            lending_id: UUID of the lending record to close.
            staff_id: UUID of the staff member processing the return.

        Returns:
            The updated LendingRecord with ``returned_at`` set.

        Raises:
            LendingNotFoundException: If no lending record exists for the id.
            AlreadyReturnedException: If the book was already returned.
        """
        try:
            lending = await LendingRepository.get_by_id_for_update(db, lending_id)
            if lending is None:
                raise LendingNotFoundException()

            if lending.returned_at is not None:
                raise AlreadyReturnedException()

            lending = await LendingRepository.mark_returned(db, lending, staff_id)

            book = await BookRepository.get_by_id_for_update(
                db,
                lending.book_id,
                include_inactive=True,
            )
            if book is not None and book.copies_available < book.copies_total:
                await BookRepository.increment_copies(db, book)
            updated_id = lending.id
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        loaded = await LendingRepository.get_by_id(db, updated_id)
        lending = loaded if loaded is not None else lending
        library_api.info("Book returned: lending %s", lending_id)
        return lending

    @staticmethod
    async def update_due_date(
        db: AsyncSession,
        lending_id: UUID,
        due_date: datetime,
        staff_id: UUID,
    ) -> LendingRecord:
        """Change the due date on an active (not yet returned) loan.

        Args:
            db: Async database session.
            lending_id: UUID of the lending record to update.
            due_date: New due datetime (converted to UTC).
            staff_id: UUID of the staff member performing the action.

        Returns:
            The updated LendingRecord.

        Raises:
            LendingNotFoundException: If no lending record exists for the id.
            HTTPException: If the loan is already returned, the due date is in
                the past, or it precedes the borrow date.
        """
        try:
            lending = await LendingRepository.get_by_id_for_update(db, lending_id)
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
            updated_id = lending.id
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        loaded = await LendingRepository.get_by_id(db, updated_id)
        lending = loaded if loaded is not None else lending
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
        """Return all lending records (active and returned) for a member.

        Args:
            db: Async database session.
            member_id: Member UUID.

        Returns:
            List of LendingRecord models ordered by borrow date.

        Raises:
            MemberNotFoundException: If the member does not exist.
        """
        await MemberService.get_by_id(db, member_id)
        return await LendingRepository.get_by_member(db, member_id)

    @staticmethod
    async def get_member_active_loans(
        db: AsyncSession,
        member_id: UUID,
    ) -> list[LendingRecord]:
        """Return only active (not yet returned) loans for a member.

        Args:
            db: Async database session.
            member_id: Member UUID.

        Returns:
            List of active LendingRecord models.

        Raises:
            MemberNotFoundException: If the member does not exist.
        """
        await MemberService.get_by_id(db, member_id)
        return await LendingRepository.get_active_by_member(db, member_id)

    @staticmethod
    async def get_history(
        db: AsyncSession,
        filters: LendingFilterParams,
    ) -> LendingHistoryResponse:
        """Return paginated, filterable lending history with page metadata.

        Args:
            db: Async database session.
            filters: Query filters, sort options, and pagination parameters.

        Returns:
            LendingHistoryResponse with items, total count, and page info.
        """
        records, total = await LendingRepository.get_history(db, filters)
        page = (filters.skip // filters.limit) + 1 if filters.limit > 0 else 1
        total_pages = math.ceil(total / filters.limit) if filters.limit > 0 else 0

        library_api.info("History fetched: %s records, filters=%s", total, filters)

        return LendingHistoryResponse(
            items=[LendingResponse.model_validate(record) for record in records],
            total=total,
            page=page,
            limit=filters.limit,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_all_active(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[LendingRecord], int]:
        """Return paginated loans that have not yet been returned.

        Args:
            db: Async database session.
            skip: Number of rows to skip.
            limit: Maximum number of rows to return.

        Returns:
            Tuple of active LendingRecord models and total matching count.
        """
        return await LendingRepository.get_all_active(db, skip=skip, limit=limit)

    @staticmethod
    async def get_overdue(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[LendingRecord], int]:
        """Return paginated active loans past their due date.

        Args:
            db: Async database session.
            skip: Number of rows to skip.
            limit: Maximum number of rows to return.

        Returns:
            Tuple of overdue LendingRecord models and total matching count.
        """
        return await LendingRepository.get_overdue(db, skip=skip, limit=limit)
