"""API routes for member management.

All routes protected by JWT authentication unless noted otherwise.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_staff, get_db
from app.models.staff import Staff
from app.schemas.lending import LendingResponse
from app.schemas.member import MemberCreate, MemberListResponse, MemberResponse, MemberUpdate
from app.services.lending_service import LendingService
from app.services.member_service import MemberService

router = APIRouter(prefix="/members", tags=["Members"])


@router.get("/", response_model=MemberListResponse)
async def list_members(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = Query(None, min_length=1, max_length=255),
    sort_by: str = Query("name", pattern="^(name|email|created_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    include_inactive: bool = False,
) -> MemberListResponse:
    """List library members with server-side pagination and filtering."""
    return await MemberService.get_page(
        db,
        page=page,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        include_inactive=include_inactive,
    )


@router.post("/", response_model=MemberResponse, status_code=201)
async def create_member(
    data: MemberCreate,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> MemberResponse:
    """Register a new library member."""
    member = await MemberService.create(db, data, current_staff.id)
    return MemberResponse.model_validate(member)


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> MemberResponse:
    """Get a single member by id."""
    member = await MemberService.get_by_id(db, member_id)
    return MemberResponse.model_validate(member)


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: UUID,
    data: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> MemberResponse:
    """Update member profile fields."""
    member = await MemberService.update(db, member_id, data, current_staff.id)
    return MemberResponse.model_validate(member)


@router.delete("/{member_id}", response_model=MemberResponse)
async def delete_member(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> MemberResponse:
    """Soft-delete a member when they have no active loans."""
    member = await MemberService.soft_delete(db, member_id, current_staff.id)
    return MemberResponse.model_validate(member)


@router.put("/{member_id}/restore", response_model=MemberResponse)
async def restore_member(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> MemberResponse:
    """Restore a previously deactivated member."""
    member = await MemberService.restore(db, member_id, current_staff.id)
    return MemberResponse.model_validate(member)


@router.get("/{member_id}/loans", response_model=list[LendingResponse])
async def get_member_loans(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> list[LendingResponse]:
    """List active (not returned) loans for a member."""
    loans = await LendingService.get_member_active_loans(db, member_id)
    return [LendingResponse.model_validate(loan) for loan in loans]
