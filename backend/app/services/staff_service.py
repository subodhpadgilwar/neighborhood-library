from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateEmailException, StaffNotFoundException
from app.core.logger import library_api
from app.core.security import verify_password
from app.models.staff import Staff
from app.repositories.staff_repo import StaffRepository
from app.schemas.staff import (
    AdminChangePasswordRequest,
    ChangePasswordRequest,
    StaffCreate,
    StaffUpdate,
)


class StaffService:
    @staticmethod
    async def get_all(
        db: AsyncSession,
        include_inactive: bool = False,
    ) -> list[Staff]:
        return await StaffRepository.get_all(db, include_inactive=include_inactive)

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        staff_id: UUID,
        include_inactive: bool = False,
    ) -> Staff:
        staff = await StaffRepository.get_by_id(
            db,
            staff_id,
            include_inactive=include_inactive,
        )
        if staff is None:
            raise StaffNotFoundException()
        return staff

    @staticmethod
    async def create(
        db: AsyncSession,
        data: StaffCreate,
        current_staff: Staff,
    ) -> Staff:
        email = str(data.email)
        existing = await StaffRepository.get_by_email(db, email)
        if existing is not None:
            raise DuplicateEmailException(email)

        staff = await StaffRepository.create(db, data)
        library_api.info(
            "Staff created: %s by %s",
            staff.email,
            current_staff.email,
        )
        return staff

    @staticmethod
    async def update(
        db: AsyncSession,
        staff_id: UUID,
        data: StaffUpdate,
        current_staff: Staff,
    ) -> Staff:
        staff = await StaffRepository.get_by_id(db, staff_id)
        if staff is None:
            raise StaffNotFoundException()

        if data.email is not None:
            new_email = str(data.email)
            if new_email != staff.email:
                existing = await StaffRepository.get_by_email(db, new_email)
                if existing is not None:
                    raise DuplicateEmailException(new_email)

        staff = await StaffRepository.update(db, staff, data)
        library_api.info(
            "Staff updated: %s by %s",
            staff.email,
            current_staff.email,
        )
        return staff

    @staticmethod
    async def change_own_password(
        db: AsyncSession,
        staff: Staff,
        data: ChangePasswordRequest,
    ) -> Staff:
        if not verify_password(data.current_password, staff.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        if verify_password(data.new_password, staff.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must differ from current",
            )

        staff = await StaffRepository.update_password(db, staff, data.new_password)
        library_api.info("Password changed for: %s", staff.email)
        return staff

    @staticmethod
    async def admin_change_password(
        db: AsyncSession,
        staff_id: UUID,
        data: AdminChangePasswordRequest,
        current_staff: Staff,
    ) -> Staff:
        staff = await StaffRepository.get_by_id(db, staff_id)
        if staff is None:
            raise StaffNotFoundException()

        staff = await StaffRepository.update_password(db, staff, data.new_password)
        library_api.info(
            "Admin %s changed password for %s",
            current_staff.email,
            staff.email,
        )
        return staff

    @staticmethod
    async def soft_delete(
        db: AsyncSession,
        staff_id: UUID,
        current_staff: Staff,
    ) -> Staff:
        staff = await StaffRepository.get_by_id(db, staff_id)
        if staff is None:
            raise StaffNotFoundException()

        if staff.is_default_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the default admin",
            )

        if staff.id == current_staff.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account",
            )

        staff = await StaffRepository.soft_delete(db, staff)
        library_api.info(
            "Staff soft deleted: %s by %s",
            staff.email,
            current_staff.email,
        )
        return staff

    @staticmethod
    async def restore(
        db: AsyncSession,
        staff_id: UUID,
        current_staff: Staff,
    ) -> Staff:
        staff = await StaffRepository.get_by_id(db, staff_id, include_inactive=True)
        if staff is None:
            raise StaffNotFoundException()

        staff = await StaffRepository.restore(db, staff)
        library_api.info(
            "Staff restored: %s by %s",
            staff.email,
            current_staff.email,
        )
        return staff
