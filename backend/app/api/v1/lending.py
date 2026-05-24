from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_staff, get_db
from app.models.staff import Staff
from app.schemas.lending import BorrowRequest, LendingResponse
from app.services.lending_service import LendingService

router = APIRouter(prefix="/lending", tags=["Lending"])


@router.post(
    "/borrow",
    response_model=LendingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def borrow_book(
    data: BorrowRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> LendingResponse:
    lending = await LendingService.borrow_book(
        db,
        data.book_id,
        data.member_id,
        current_staff.id,
    )
    return LendingResponse.model_validate(lending)


@router.put("/{lending_id}/return", response_model=LendingResponse)
async def return_book(
    lending_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> LendingResponse:
    lending = await LendingService.return_book(db, lending_id, current_staff.id)
    return LendingResponse.model_validate(lending)


@router.get("/", response_model=list[LendingResponse])
async def list_active_loans(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> list[LendingResponse]:
    loans = await LendingService.get_all_active(db)
    return [LendingResponse.model_validate(loan) for loan in loans]


@router.get("/overdue", response_model=list[LendingResponse])
async def list_overdue_loans(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> list[LendingResponse]:
    loans = await LendingService.get_overdue(db)
    return [LendingResponse.model_validate(loan) for loan in loans]
