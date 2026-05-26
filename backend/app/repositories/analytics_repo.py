"""Repository layer for analytics database operations. Contains only database queries — no business logic. All business rules belong in the service layer."""

from datetime import timedelta
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import library_api
from app.config import settings
from app.core.timezone import get_app_timezone, now_utc, start_of_month_local, subtract_months, to_utc
from app.models.book import Book
from app.models.lending import LendingRecord
from app.models.member import Member


class AnalyticsRepository:
    """Data access layer for read-only analytics aggregations."""

    @staticmethod
    async def get_genre_distribution(db: AsyncSession) -> list[dict[str, Any]]:
        """Aggregate active book inventory counts grouped by genre.

        Args:
            db: Async database session.

        Returns:
            List of dicts with genre, total_books, total_copies, and available_copies.
            Only active books (``Book.is_active``) are included.
        """
        library_api.debug("AnalyticsRepository.get_genre_distribution")
        genre_label = func.coalesce(Book.genre, "Uncategorized").label("genre")
        stmt = (
            select(
                genre_label,
                func.count(Book.id).label("total_books"),
                func.coalesce(func.sum(Book.copies_total), 0).label("total_copies"),
                func.coalesce(func.sum(Book.copies_available), 0).label("available_copies"),
            )
            .where(Book.is_active.is_(True))
            .group_by(genre_label)
            .order_by(func.count(Book.id).desc())
        )
        result = await db.execute(stmt)
        return [
            {
                "genre": row.genre,
                "total_books": int(row.total_books),
                "total_copies": int(row.total_copies),
                "available_copies": int(row.available_copies),
            }
            for row in result.all()
        ]

    @staticmethod
    async def get_monthly_lending(db: AsyncSession, months: int = 6) -> list[dict[str, Any]]:
        """Aggregate lending activity by calendar month in the app timezone.

        Args:
            db: Async database session.
            months: Number of months to include, counting back from the current month.

        Returns:
            List of dicts with month, total_loans, returned_loans, and overdue_loans.
            Overdue counts reflect loans still open and past due at query time.
        """
        library_api.debug("AnalyticsRepository.get_monthly_lending months=%s", months)
        local_borrowed = func.timezone(settings.app_timezone, LendingRecord.borrowed_at)
        month_bucket = func.date_trunc("month", local_borrowed).label("month")
        current_time = now_utc()
        cutoff_local = subtract_months(start_of_month_local(current_time), months - 1)
        cutoff = to_utc(cutoff_local)
        assert cutoff is not None

        returned_expr = func.sum(
            case((LendingRecord.returned_at.is_not(None), 1), else_=0)
        ).label("returned_loans")
        overdue_expr = func.sum(
            case(
                (
                    and_(
                        LendingRecord.returned_at.is_(None),
                        LendingRecord.due_date < current_time,
                    ),
                    1,
                ),
                else_=0,
            )
        ).label("overdue_loans")

        stmt = (
            select(
                month_bucket,
                func.count(LendingRecord.id).label("total_loans"),
                returned_expr,
                overdue_expr,
            )
            .where(LendingRecord.borrowed_at >= cutoff)
            .group_by(month_bucket)
            .order_by(month_bucket.asc())
        )
        result = await db.execute(stmt)
        return [
            {
                "month": row.month,
                "total_loans": int(row.total_loans),
                "returned_loans": int(row.returned_loans or 0),
                "overdue_loans": int(row.overdue_loans or 0),
            }
            for row in result.all()
        ]

    @staticmethod
    async def get_top_borrowed_books(
        db: AsyncSession,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Fetch the most-borrowed active books by total loan count.

        Args:
            db: Async database session.
            limit: Maximum number of books to return.

        Returns:
            List of dicts with book metadata and total_borrows/current_borrows counts.
            Only active books (``Book.is_active``) are included.
        """
        library_api.debug("AnalyticsRepository.get_top_borrowed_books limit=%s", limit)
        total_borrows = func.count(LendingRecord.id).label("total_borrows")
        current_borrows = func.sum(
            case((LendingRecord.returned_at.is_(None), 1), else_=0)
        ).label("current_borrows")

        stmt = (
            select(
                Book.id,
                Book.title,
                Book.author,
                Book.genre,
                Book.shelf_location,
                Book.copies_total,
                Book.copies_available,
                total_borrows,
                current_borrows,
            )
            .outerjoin(LendingRecord, LendingRecord.book_id == Book.id)
            .where(Book.is_active.is_(True))
            .group_by(Book.id)
            .order_by(total_borrows.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return [
            {
                "id": row.id,
                "title": row.title,
                "author": row.author,
                "genre": row.genre,
                "shelf_location": row.shelf_location,
                "copies_total": int(row.copies_total),
                "copies_available": int(row.copies_available),
                "total_borrows": int(row.total_borrows),
                "current_borrows": int(row.current_borrows or 0),
            }
            for row in result.all()
        ]

    @staticmethod
    async def _count_scalar(db: AsyncSession, stmt) -> int:
        """Execute a scalar count/sum query and coerce the result to int.

        Args:
            db: Async database session.
            stmt: SQLAlchemy select statement returning a single scalar value.

        Returns:
            Integer result, or 0 if the scalar is None.
        """
        result = await db.execute(stmt)
        value = result.scalar_one()
        return int(value or 0)

    @staticmethod
    async def get_summary_stats(db: AsyncSession) -> dict[str, int]:
        """Fetch dashboard summary counts across books, members, and loans.

        Args:
            db: Async database session.

        Returns:
            Dict with total_books, total_members, active_loans, overdue_loans,
            total_copies, available_copies, loans_today, and returns_today.
            Book and member totals count only active records; today metrics use
            the application local timezone day boundary.
        """
        library_api.debug("AnalyticsRepository.get_summary_stats")
        current_time = now_utc()
        app_tz = get_app_timezone()
        today_start_local = current_time.astimezone(app_tz).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        today_end_local = today_start_local + timedelta(days=1)
        today_start = today_start_local.astimezone(current_time.tzinfo)
        today_end = today_end_local.astimezone(current_time.tzinfo)

        total_books_stmt = select(func.count(Book.id)).where(Book.is_active.is_(True))
        total_members_stmt = select(func.count(Member.id)).where(Member.is_active.is_(True))
        active_loans_stmt = select(func.count(LendingRecord.id)).where(
            LendingRecord.returned_at.is_(None)
        )
        overdue_loans_stmt = select(func.count(LendingRecord.id)).where(
            LendingRecord.returned_at.is_(None),
            LendingRecord.due_date < current_time,
        )
        total_copies_stmt = select(func.coalesce(func.sum(Book.copies_total), 0)).where(
            Book.is_active.is_(True)
        )
        available_copies_stmt = select(
            func.coalesce(func.sum(Book.copies_available), 0)
        ).where(Book.is_active.is_(True))
        loans_today_stmt = select(func.count(LendingRecord.id)).where(
            LendingRecord.borrowed_at >= today_start,
            LendingRecord.borrowed_at < today_end,
        )
        returns_today_stmt = select(func.count(LendingRecord.id)).where(
            LendingRecord.returned_at.is_not(None),
            LendingRecord.returned_at >= today_start,
            LendingRecord.returned_at < today_end,
        )

        total_books = await AnalyticsRepository._count_scalar(db, total_books_stmt)
        total_members = await AnalyticsRepository._count_scalar(db, total_members_stmt)
        active_loans = await AnalyticsRepository._count_scalar(db, active_loans_stmt)
        overdue_loans = await AnalyticsRepository._count_scalar(db, overdue_loans_stmt)
        total_copies = await AnalyticsRepository._count_scalar(db, total_copies_stmt)
        available_copies = await AnalyticsRepository._count_scalar(
            db,
            available_copies_stmt,
        )
        loans_today = await AnalyticsRepository._count_scalar(db, loans_today_stmt)
        returns_today = await AnalyticsRepository._count_scalar(db, returns_today_stmt)

        return {
            "total_books": total_books,
            "total_members": total_members,
            "active_loans": active_loans,
            "overdue_loans": overdue_loans,
            "total_copies": total_copies,
            "available_copies": available_copies,
            "loans_today": loans_today,
            "returns_today": returns_today,
        }
