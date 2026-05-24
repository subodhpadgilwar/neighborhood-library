from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_staff, get_db
from app.models.staff import Staff
from app.schemas.analytics import (
    GenreStats,
    MonthlyLendingStats,
    SummaryStatsResponse,
    TopBookStats,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/genre-distribution", response_model=list[GenreStats])
async def genre_distribution(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> list[GenreStats]:
    return await AnalyticsService.get_genre_distribution(db)


@router.get("/monthly-lending", response_model=list[MonthlyLendingStats])
async def monthly_lending(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
    months: int = Query(6, ge=1, le=24),
) -> list[MonthlyLendingStats]:
    return await AnalyticsService.get_monthly_lending(db, months=months)


@router.get("/top-books", response_model=list[TopBookStats])
async def top_borrowed_books(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
    limit: int = Query(5, ge=3, le=20),
) -> list[TopBookStats]:
    return await AnalyticsService.get_top_borrowed_books(db, limit=limit)


@router.get("/summary", response_model=SummaryStatsResponse)
async def summary_stats(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> SummaryStatsResponse:
    return await AnalyticsService.get_summary_stats(db)
