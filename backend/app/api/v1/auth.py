from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_staff, get_db
from app.core.exceptions import DuplicateEmailException, InvalidCredentialsException
from app.core.security import create_access_token, hash_password
from app.models.staff import Staff
from app.schemas.auth import StaffCreate, StaffResponse, TokenResponse
from app.services.auth_service import authenticate_staff, get_staff_by_email

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
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
    _current_staff: Staff = Depends(get_current_staff),
) -> Staff:
    email = str(data.email)
    existing = await get_staff_by_email(db, email)
    if existing is not None:
        raise DuplicateEmailException(email)

    staff = Staff(
        email=email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(staff)
    await db.commit()
    await db.refresh(staff)
    return staff


@router.get("/me", response_model=StaffResponse)
async def get_me(
    current_staff: Staff = Depends(get_current_staff),
) -> Staff:
    return current_staff
