"""Service layer for analytics business logic.

Orchestrates between repository layer and API layer. All business rules and
validation that requires database context live here.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezone import (
    format_month_label,
    month_key,
    start_of_month_local,
    subtract_months,
)
from app.repositories.analytics_repo import AnalyticsRepository
from app.schemas.analytics import (
    GenreStats,
    MonthlyLendingStats,
    SummaryStatsResponse,
    TopBookStats,
)


class AnalyticsService:
    """Business logic for dashboard and reporting aggregates."""

    @staticmethod
    async def get_genre_distribution(db: AsyncSession) -> list[GenreStats]:
        """Compute per-genre book and copy counts with percentage share.

        Args:
            db: Async database session.

        Returns:
            List of GenreStats with totals and percentage of catalog.
        """
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
        """Build monthly loan activity for the last N calendar months.

        Missing months in the repository result are filled with zero counts.
        Active loans per month are derived as total minus returned.

        Args:
            db: Async database session.
            months: Number of months to include (default 6).

        Returns:
            Chronologically ordered list of MonthlyLendingStats.
        """
        rows = await AnalyticsRepository.get_monthly_lending(db, months=months)
        rows_by_month = {month_key(row["month"]): row for row in rows}

        month_starts: list = []
        cursor = start_of_month_local()
        for _ in range(months):
            month_starts.append(cursor)
            cursor = subtract_months(cursor, 1)
        month_starts.sort()

        result: list[MonthlyLendingStats] = []
        for month_start in month_starts:
            key = month_key(month_start)
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
            year, month = key
            result.append(
                MonthlyLendingStats(
                    month=format_month_label(year, month),
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
        """Return the most-borrowed books with utilization rates.

        Args:
            db: Async database session.
            limit: Maximum number of books to return (default 5).

        Returns:
            List of TopBookStats ranked by total borrows.
        """
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
        """Return high-level counts for books, members, loans, and overdue items.

        Args:
            db: Async database session.

        Returns:
            SummaryStatsResponse with aggregate dashboard figures.
        """
        data = await AnalyticsRepository.get_summary_stats(db)
        return SummaryStatsResponse(**data)
