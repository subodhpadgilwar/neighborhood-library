"""API routes for lending management.

All routes protected by JWT authentication unless noted otherwise.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_staff, get_db
from app.models.staff import Staff
from app.schemas.lending import (
    BorrowRequest,
    LendingFilterParams,
    LendingHistoryResponse,
    LendingResponse,
    UpdateDueDateRequest,
)
from app.services.lending_service import LendingService

router = APIRouter(prefix="/lending", tags=["Lending"])


@router.post(
    "/borrow",
    response_model=LendingResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def borrow_book(
    data: BorrowRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> LendingResponse:
    """Borrow a book for a member; optional custom due date in request body."""
    lending = await LendingService.borrow_book(
        db,
        data.book_id,
        data.member_id,
        current_staff.id,
        due_date=data.due_date,
    )
    return LendingResponse.model_validate(lending)


@router.get("/history", response_model=LendingHistoryResponse)
async def lending_history(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
    status: Optional[str] = Query(None),
    member_name: Optional[str] = Query(None),
    book_title: Optional[str] = Query(None),
    borrowed_from: Optional[datetime] = Query(None),
    borrowed_to: Optional[datetime] = Query(None),
    sort_by: Optional[str] = Query("borrowed_at"),
    sort_order: Optional[str] = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> LendingHistoryResponse:
    """Return paginated lending history with status, name, date, and sort filters."""
    filters = LendingFilterParams(
        status=status,  # type: ignore[arg-type]
        member_name=member_name,
        book_title=book_title,
        borrowed_from=borrowed_from,
        borrowed_to=borrowed_to,
        sort_by=sort_by,  # type: ignore[arg-type]
        sort_order=sort_order,  # type: ignore[arg-type]
        skip=skip,
        limit=limit,
    )
    return await LendingService.get_history(db, filters)


@router.get("/", response_model=list[LendingResponse])
async def list_active_loans(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> list[LendingResponse]:
    """List all loans that have not yet been returned."""
    loans = await LendingService.get_all_active(db)
    return [LendingResponse.model_validate(loan) for loan in loans]


@router.get("/overdue", response_model=list[LendingResponse])
async def list_overdue_loans(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> list[LendingResponse]:
    """List active loans past their due date."""
    loans = await LendingService.get_overdue(db)
    return [LendingResponse.model_validate(loan) for loan in loans]


@router.put("/{lending_id}/due-date", response_model=LendingResponse)
async def update_due_date(
    lending_id: UUID,
    data: UpdateDueDateRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> LendingResponse:
    """Update the due date on an active loan."""
    lending = await LendingService.update_due_date(
        db,
        lending_id,
        data.due_date,
        current_staff.id,
    )
    return LendingResponse.model_validate(lending)


@router.put("/{lending_id}/return", response_model=LendingResponse)
async def return_book(
    lending_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> LendingResponse:
    """Mark a loan as returned and increment available copies."""
    lending = await LendingService.return_book(db, lending_id, current_staff.id)
    return LendingResponse.model_validate(lending)
