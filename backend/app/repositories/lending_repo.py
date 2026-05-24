"""Repository layer for lending database operations. Contains only database queries — no business logic. All business rules belong in the service layer."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from app.core.logger import library_api
from app.core.timezone import now_utc, to_utc
from app.models.book import Book
from app.models.lending import LendingRecord
from app.models.member import Member
from app.schemas.lending import LendingFilterParams

_LENDING_LOAD_OPTIONS = (
    selectinload(LendingRecord.book),
    selectinload(LendingRecord.member),
    selectinload(LendingRecord.created_by_staff),
)


class LendingRepository:
    """Data access layer for LendingRecord entities."""

    @staticmethod
    def _select_lending():
        """Build a base SELECT for lending records with related entities loaded.

        Returns:
            SQLAlchemy select statement with book, member, and staff eager-loaded.
        """
        return select(LendingRecord).options(*_LENDING_LOAD_OPTIONS)

    @staticmethod
    async def get_by_id(db: AsyncSession, lending_id: UUID) -> LendingRecord | None:
        """Fetch a single lending record by primary key.

        Args:
            db: Async database session.
            lending_id: Lending record UUID.

        Returns:
            The matching LendingRecord with relationships loaded, or None.
        """
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
        """Fetch all unreturned loans for a book.

        Args:
            db: Async database session.
            book_id: Book UUID.

        Returns:
            List of active LendingRecord rows for the book.
        """
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
        """Fetch an active loan for a specific book and member pair.

        Args:
            db: Async database session.
            book_id: Book UUID.
            member_id: Member UUID.

        Returns:
            The active LendingRecord, or None if no open loan exists.
        """
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
        """Fetch all lending records for a member, newest first.

        Args:
            db: Async database session.
            member_id: Member UUID.

        Returns:
            List of LendingRecord rows ordered by borrowed_at descending.
        """
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
        """Fetch unreturned loans for a member, newest first.

        Args:
            db: Async database session.
            member_id: Member UUID.

        Returns:
            List of active LendingRecord rows ordered by borrowed_at descending.
        """
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
        """Fetch all unreturned lending records.

        Args:
            db: Async database session.

        Returns:
            List of active LendingRecord rows with relationships loaded.
        """
        library_api.debug("LendingRepository.get_all_active")
        result = await db.execute(
            LendingRepository._select_lending().where(
                LendingRecord.returned_at.is_(None)
            )
        )
        return list(result.scalars().all())

    @staticmethod
    def _apply_history_joins(
        stmt: Select,
        filters: LendingFilterParams,
    ) -> tuple[Select, bool, bool]:
        """Add Member and/or Book joins required by filters or sort columns.

        Args:
            stmt: Base select or count statement.
            filters: Lending history filter and sort parameters.

        Returns:
            Tuple of the modified statement, whether Member was joined, and
            whether Book was joined.
        """
        needs_member_join = bool(filters.member_name) or filters.sort_by == "member_name"
        needs_book_join = bool(filters.book_title) or filters.sort_by == "book_title"

        if needs_member_join:
            stmt = stmt.join(Member, LendingRecord.member_id == Member.id)
        if needs_book_join:
            stmt = stmt.join(Book, LendingRecord.book_id == Book.id)

        return stmt, needs_member_join, needs_book_join

    @staticmethod
    def _apply_history_filters(
        stmt: Select,
        filters: LendingFilterParams,
        *,
        needs_member_join: bool,
        needs_book_join: bool,
    ) -> Select:
        """Apply status, name/title, and date-range filters to a history query.

        Args:
            stmt: Select or count statement to filter.
            filters: Lending history filter parameters.
            needs_member_join: Whether Member is already joined on the statement.
            needs_book_join: Whether Book is already joined on the statement.

        Returns:
            The filtered statement. Status ``overdue`` matches unreturned loans past due_date.
        """
        if filters.status == "active":
            stmt = stmt.where(LendingRecord.returned_at.is_(None))
        elif filters.status == "returned":
            stmt = stmt.where(LendingRecord.returned_at.is_not(None))
        elif filters.status == "overdue":
            stmt = stmt.where(
                LendingRecord.returned_at.is_(None),
                LendingRecord.due_date < now_utc(),
            )

        if filters.member_name:
            if not needs_member_join:
                stmt = stmt.join(Member, LendingRecord.member_id == Member.id)
            stmt = stmt.where(Member.name.ilike(f"%{filters.member_name}%"))

        if filters.book_title:
            if not needs_book_join:
                stmt = stmt.join(Book, LendingRecord.book_id == Book.id)
            stmt = stmt.where(Book.title.ilike(f"%{filters.book_title}%"))

        if filters.borrowed_from is not None:
            borrowed_from = to_utc(filters.borrowed_from)
            if borrowed_from is not None:
                stmt = stmt.where(LendingRecord.borrowed_at >= borrowed_from)

        if filters.borrowed_to is not None:
            borrowed_to = to_utc(filters.borrowed_to)
            if borrowed_to is not None:
                stmt = stmt.where(LendingRecord.borrowed_at <= borrowed_to)

        return stmt

    @staticmethod
    def _history_sort_column(
        filters: LendingFilterParams,
        *,
        needs_member_join: bool,
        needs_book_join: bool,
    ):
        """Resolve the SQLAlchemy column used for history sorting.

        Args:
            filters: Lending history filter and sort parameters.
            needs_member_join: Whether Member is already joined on the statement.
            needs_book_join: Whether Book is already joined on the statement.

        Returns:
            SQLAlchemy column expression for the requested sort field.

        Raises:
            ValueError: If sorting by member_name or book_title without the required join.
        """
        sort_by = filters.sort_by or "borrowed_at"
        if sort_by == "due_date":
            return LendingRecord.due_date
        if sort_by == "returned_at":
            return LendingRecord.returned_at
        if sort_by == "member_name":
            if not needs_member_join:
                raise ValueError("member_name sort requires Member join")
            return Member.name
        if sort_by == "book_title":
            if not needs_book_join:
                raise ValueError("book_title sort requires Book join")
            return Book.title
        return LendingRecord.borrowed_at

    @staticmethod
    async def get_history(
        db: AsyncSession,
        filters: LendingFilterParams,
    ) -> tuple[list[LendingRecord], int]:
        """Fetch filtered, sorted, paginated lending history with total count.

        Args:
            db: Async database session.
            filters: Status, text search, date range, sort, and pagination params.

        Returns:
            Tuple of matching LendingRecord rows and total row count before pagination.
        """
        library_api.debug("LendingRepository.get_history filters=%s", filters)

        base_stmt = select(LendingRecord).options(*_LENDING_LOAD_OPTIONS)
        count_stmt = select(func.count(func.distinct(LendingRecord.id))).select_from(
            LendingRecord
        )

        base_stmt, needs_member_join, needs_book_join = LendingRepository._apply_history_joins(
            base_stmt,
            filters,
        )
        count_stmt, _, _ = LendingRepository._apply_history_joins(count_stmt, filters)

        base_stmt = LendingRepository._apply_history_filters(
            base_stmt,
            filters,
            needs_member_join=needs_member_join,
            needs_book_join=needs_book_join,
        )
        count_stmt = LendingRepository._apply_history_filters(
            count_stmt,
            filters,
            needs_member_join=needs_member_join,
            needs_book_join=needs_book_join,
        )

        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        sort_column = LendingRepository._history_sort_column(
            filters,
            needs_member_join=needs_member_join,
            needs_book_join=needs_book_join,
        )
        order_fn = asc if filters.sort_order == "asc" else desc

        result_stmt = (
            base_stmt.order_by(order_fn(sort_column))
            .offset(filters.skip)
            .limit(filters.limit)
        )
        result = await db.execute(result_stmt)
        records = list(result.scalars().unique().all())

        return records, total

    @staticmethod
    async def get_overdue(db: AsyncSession) -> list[LendingRecord]:
        """Fetch all unreturned loans past their due date.

        Args:
            db: Async database session.

        Returns:
            List of overdue LendingRecord rows with relationships loaded.
        """
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
        """Insert a new lending record.

        Args:
            db: Async database session.
            book_id: Book UUID being borrowed.
            member_id: Member UUID borrowing the book.
            staff_id: Staff UUID processing the loan.
            due_date: Loan due date in UTC.

        Returns:
            The persisted LendingRecord with relationships loaded.
        """
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
        """Update the due date on an existing lending record.

        Args:
            db: Async database session.
            lending: LendingRecord to update.
            new_due_date: New due date in UTC.
            staff_id: Staff UUID performing the update.

        Returns:
            The updated LendingRecord with relationships loaded.
        """
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
        """Set returned_at on a lending record.

        Args:
            db: Async database session.
            lending: LendingRecord to mark as returned.
            staff_id: Staff UUID processing the return.

        Returns:
            The updated LendingRecord with relationships loaded.
        """
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
