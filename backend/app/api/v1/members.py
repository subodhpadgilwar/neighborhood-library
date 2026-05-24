from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_staff, get_db
from app.models.staff import Staff
from app.schemas.lending import LendingResponse
from app.schemas.member import MemberCreate, MemberResponse, MemberUpdate
from app.services.lending_service import LendingService
from app.services.member_service import MemberService

router = APIRouter(prefix="/members", tags=["Members"])


@router.get("/", response_model=list[MemberResponse])
async def list_members(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_inactive: bool = False,
) -> list[MemberResponse]:
    members = await MemberService.get_all(
        db,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
    )
    return [MemberResponse.model_validate(member) for member in members]


@router.post("/", response_model=MemberResponse, status_code=201)
async def create_member(
    data: MemberCreate,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> MemberResponse:
    member = await MemberService.create(db, data, current_staff.id)
    return MemberResponse.model_validate(member)


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> MemberResponse:
    member = await MemberService.get_by_id(db, member_id)
    return MemberResponse.model_validate(member)


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: UUID,
    data: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> MemberResponse:
    member = await MemberService.update(db, member_id, data, current_staff.id)
    return MemberResponse.model_validate(member)


@router.delete("/{member_id}", response_model=MemberResponse)
async def delete_member(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> MemberResponse:
    member = await MemberService.soft_delete(db, member_id, current_staff.id)
    return MemberResponse.model_validate(member)


@router.put("/{member_id}/restore", response_model=MemberResponse)
async def restore_member(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> MemberResponse:
    member = await MemberService.restore(db, member_id, current_staff.id)
    return MemberResponse.model_validate(member)


@router.get("/{member_id}/loans", response_model=list[LendingResponse])
async def get_member_loans(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> list[LendingResponse]:
    loans = await LendingService.get_member_active_loans(db, member_id)
    return [LendingResponse.model_validate(loan) for loan in loans]
