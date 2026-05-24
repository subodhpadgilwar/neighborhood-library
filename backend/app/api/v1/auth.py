"""API routes for authentication management.

All routes protected by JWT authentication unless noted otherwise.
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_staff, get_db
from app.core.exceptions import InvalidCredentialsException
from app.core.security import create_access_token
from app.models.staff import Staff
from app.schemas.auth import TokenResponse
from app.schemas.staff import StaffCreate, StaffResponse
from app.services.auth_service import authenticate_staff
from app.services.staff_service import StaffService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange staff credentials for a JWT access token (no auth required)."""
    staff = await authenticate_staff(
        db,
        form_data.username,
        form_data.password,
    )
    if staff is None:
        raise InvalidCredentialsException()

    access_token = create_access_token({"sub": str(staff.id)})
    return TokenResponse(access_token=access_token)


@router.post(
    "/register",
    response_model=StaffResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: StaffCreate,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> StaffResponse:
    """Register a new staff account; requires an authenticated staff JWT."""
    staff = await StaffService.create(db, data, current_staff)
    return StaffResponse.model_validate(staff)


@router.get("/me", response_model=StaffResponse)
async def get_me(
    current_staff: Staff = Depends(get_current_staff),
) -> StaffResponse:
    """Return the profile of the currently authenticated staff member."""
    return StaffResponse.model_validate(current_staff)
