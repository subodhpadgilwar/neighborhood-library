from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezone import UTC, to_local
from app.repositories.analytics_repo import AnalyticsRepository, _subtract_months
from app.schemas.analytics import (
    GenreStats,
    MonthlyLendingStats,
    SummaryStatsResponse,
    TopBookStats,
)


class AnalyticsService:
    @staticmethod
    async def get_genre_distribution(db: AsyncSession) -> list[GenreStats]:
        rows = await AnalyticsRepository.get_genre_distribution(db)
        total_books = sum(row["total_books"] for row in rows)

        stats: list[GenreStats] = []
        for row in rows:
            percentage = (
                round((row["total_books"] / total_books) * 100, 1) if total_books > 0 else 0.0
            )
            stats.append(
                GenreStats(
                    genre=row["genre"],
                    total_books=row["total_books"],
                    total_copies=row["total_copies"],
                    available_copies=row["available_copies"],
                    percentage=percentage,
                )
            )
        return stats

    @staticmethod
    async def get_monthly_lending(
        db: AsyncSession,
        months: int = 6,
    ) -> list[MonthlyLendingStats]:
        rows = await AnalyticsRepository.get_monthly_lending(db, months=months)
        rows_by_month = {
            _normalize_month_key(row["month"]): row for row in rows
        }

        current = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_starts: list[datetime] = []
        cursor = current
        for _ in range(months):
            month_starts.append(cursor)
            cursor = _subtract_months(cursor, 1).replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        month_starts.sort()

        result: list[MonthlyLendingStats] = []
        for month_start in month_starts:
            key = _normalize_month_key(month_start)
            row = rows_by_month.get(
                key,
                {
                    "total_loans": 0,
                    "returned_loans": 0,
                    "overdue_loans": 0,
                },
            )
            total_loans = int(row["total_loans"])
            returned_loans = int(row["returned_loans"])
            overdue_loans = int(row["overdue_loans"])
            local_month = to_local(month_start)
            assert local_month is not None
            result.append(
                MonthlyLendingStats(
                    month=local_month.strftime("%b %Y"),
                    total_loans=total_loans,
                    returned_loans=returned_loans,
                    overdue_loans=overdue_loans,
                    active_loans=total_loans - returned_loans,
                )
            )
        return result

    @staticmethod
    async def get_top_borrowed_books(
        db: AsyncSession,
        limit: int = 5,
    ) -> list[TopBookStats]:
        rows = await AnalyticsRepository.get_top_borrowed_books(db, limit=limit)
        stats: list[TopBookStats] = []
        for row in rows:
            copies_total = row["copies_total"]
            current_borrows = row["current_borrows"]
            if copies_total == 0:
                utilization_rate = 0.0
            else:
                utilization_rate = round((current_borrows / copies_total) * 100, 1)
            stats.append(
                TopBookStats(
                    id=row["id"],
                    title=row["title"],
                    author=row["author"],
                    genre=row["genre"],
                    shelf_location=row["shelf_location"],
                    copies_total=copies_total,
                    copies_available=row["copies_available"],
                    total_borrows=row["total_borrows"],
                    current_borrows=current_borrows,
                    utilization_rate=utilization_rate,
                )
            )
        return stats

    @staticmethod
    async def get_summary_stats(db: AsyncSession) -> SummaryStatsResponse:
        data = await AnalyticsRepository.get_summary_stats(db)
        return SummaryStatsResponse(**data)


def _normalize_month_key(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = UTC.localize(value)
    else:
        value = value.astimezone(UTC)
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
