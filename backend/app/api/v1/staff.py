"""API routes for staff management.

All routes protected by JWT authentication unless noted otherwise.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_staff, get_db
from app.models.staff import Staff
from app.schemas.staff import (
    AdminChangePasswordRequest,
    ChangePasswordRequest,
    StaffCreate,
    StaffResponse,
    StaffUpdate,
)
from app.services.staff_service import StaffService

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.get("/", response_model=list[StaffResponse])
async def list_staff(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
    include_inactive: bool = False,
) -> list[StaffResponse]:
    """List staff accounts with optional inclusion of deactivated users."""
    staff_list = await StaffService.get_all(db, include_inactive=include_inactive)
    return [StaffResponse.model_validate(staff) for staff in staff_list]


@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    data: StaffCreate,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> StaffResponse:
    """Create a new staff account."""
    staff = await StaffService.create(db, data, current_staff)
    return StaffResponse.model_validate(staff)


@router.put("/me/change-password", response_model=StaffResponse)
async def change_own_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> StaffResponse:
    """Change the authenticated staff member's own password."""
    staff = await StaffService.change_own_password(db, current_staff, data)
    return StaffResponse.model_validate(staff)


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> StaffResponse:
    """Get a single staff account by id."""
    staff = await StaffService.get_by_id(db, staff_id)
    return StaffResponse.model_validate(staff)


@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: UUID,
    data: StaffUpdate,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> StaffResponse:
    """Update another staff member's profile fields."""
    staff = await StaffService.update(db, staff_id, data, current_staff)
    return StaffResponse.model_validate(staff)


@router.delete("/{staff_id}", response_model=StaffResponse)
async def delete_staff(
    staff_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> StaffResponse:
    """Deactivate a staff account; blocks default admin and self-deactivation."""
    staff = await StaffService.soft_delete(db, staff_id, current_staff)
    return StaffResponse.model_validate(staff)


@router.put("/{staff_id}/restore", response_model=StaffResponse)
async def restore_staff(
    staff_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> StaffResponse:
    """Restore a previously deactivated staff account."""
    staff = await StaffService.restore(db, staff_id, current_staff)
    return StaffResponse.model_validate(staff)


@router.put("/{staff_id}/change-password", response_model=StaffResponse)
async def admin_change_password(
    staff_id: UUID,
    data: AdminChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> StaffResponse:
    """Reset another staff member's password (admin action)."""
    staff = await StaffService.admin_change_password(db, staff_id, data, current_staff)
    return StaffResponse.model_validate(staff)
