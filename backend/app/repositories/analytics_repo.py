import asyncio
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import library_api
from app.core.timezone import UTC, now_utc
from app.models.book import Book
from app.models.lending import LendingRecord
from app.models.member import Member


class AnalyticsRepository:
    @staticmethod
    async def get_genre_distribution(db: AsyncSession) -> list[dict[str, Any]]:
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
        library_api.debug("AnalyticsRepository.get_monthly_lending months=%s", months)
        month_bucket = func.date_trunc("month", LendingRecord.borrowed_at).label("month")
        current_time = now_utc()
        cutoff = _subtract_months(current_time, months - 1).replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

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
        result = await db.execute(stmt)
        value = result.scalar_one()
        return int(value or 0)

    @staticmethod
    async def get_summary_stats(db: AsyncSession) -> dict[str, int]:
        library_api.debug("AnalyticsRepository.get_summary_stats")
        current_time = now_utc()
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

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

        (
            total_books,
            total_members,
            active_loans,
            overdue_loans,
            total_copies,
            available_copies,
            loans_today,
            returns_today,
        ) = await asyncio.gather(
            AnalyticsRepository._count_scalar(db, total_books_stmt),
            AnalyticsRepository._count_scalar(db, total_members_stmt),
            AnalyticsRepository._count_scalar(db, active_loans_stmt),
            AnalyticsRepository._count_scalar(db, overdue_loans_stmt),
            AnalyticsRepository._count_scalar(db, total_copies_stmt),
            AnalyticsRepository._count_scalar(db, available_copies_stmt),
            AnalyticsRepository._count_scalar(db, loans_today_stmt),
            AnalyticsRepository._count_scalar(db, returns_today_stmt),
        )

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


def _subtract_months(dt: datetime, months: int) -> datetime:
    year = dt.year
    month = dt.month - months
    while month <= 0:
        month += 12
        year -= 1
    return dt.replace(year=year, month=month)
