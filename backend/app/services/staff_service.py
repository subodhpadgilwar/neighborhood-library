"""Service layer for staff business logic.

Orchestrates between repository layer and API layer. All business rules and
validation that requires database context live here.
"""

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
    """Business logic for library staff account operations."""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        include_inactive: bool = False,
    ) -> list[Staff]:
        """Return all staff accounts, optionally including deactivated users.

        Args:
            db: Async database session.
            include_inactive: When True, include soft-deleted staff.

        Returns:
            List of Staff models.
        """
        return await StaffRepository.get_all(db, include_inactive=include_inactive)

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        staff_id: UUID,
        include_inactive: bool = False,
    ) -> Staff:
        """Fetch a single staff account by primary key.

        Args:
            db: Async database session.
            staff_id: Staff UUID.
            include_inactive: When True, allow loading a deactivated account.

        Returns:
            The Staff model.

        Raises:
            StaffNotFoundException: If no staff account exists for the given id.
        """
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
        """Create a new staff account (admin-only).

        Args:
            db: Async database session.
            data: Staff creation payload.
            current_staff: Authenticated staff performing the action.

        Returns:
            The persisted Staff model.

        Raises:
            DuplicateEmailException: If the email is already registered.
        """
        email = str(data.email)
        try:
            existing = await StaffRepository.get_by_email(db, email)
            if existing is not None:
                raise DuplicateEmailException(email)

            staff = await StaffRepository.create(db, data)
            await db.commit()
            await db.refresh(staff)
        except Exception:
            await db.rollback()
            raise
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
        """Update an existing staff account's profile fields.

        Args:
            db: Async database session.
            staff_id: Staff UUID to update.
            data: Partial update payload.
            current_staff: Authenticated staff performing the action.

        Returns:
            The updated Staff model.

        Raises:
            StaffNotFoundException: If the staff account does not exist.
            DuplicateEmailException: If the new email belongs to another account.
        """
        try:
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
            await db.commit()
            await db.refresh(staff)
        except Exception:
            await db.rollback()
            raise
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
        """Change the authenticated staff member's own password.

        Args:
            db: Async database session.
            staff: Currently authenticated Staff model.
            data: Current and new password values.

        Returns:
            The Staff model with an updated password hash.

        Raises:
            HTTPException: If the current password is wrong or matches the new one.
        """
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

        try:
            staff = await StaffRepository.update_password(db, staff, data.new_password)
            await db.commit()
            await db.refresh(staff)
        except Exception:
            await db.rollback()
            raise
        library_api.info("Password changed for: %s", staff.email)
        return staff

    @staticmethod
    async def admin_change_password(
        db: AsyncSession,
        staff_id: UUID,
        data: AdminChangePasswordRequest,
        current_staff: Staff,
    ) -> Staff:
        """Reset another staff member's password (admin action).

        Args:
            db: Async database session.
            staff_id: Target staff UUID.
            data: New password payload.
            current_staff: Authenticated admin performing the action.

        Returns:
            The Staff model with an updated password hash.

        Raises:
            StaffNotFoundException: If the target staff account does not exist.
        """
        try:
            staff = await StaffRepository.get_by_id(db, staff_id)
            if staff is None:
                raise StaffNotFoundException()

            staff = await StaffRepository.update_password(db, staff, data.new_password)
            await db.commit()
            await db.refresh(staff)
        except Exception:
            await db.rollback()
            raise
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
        """Deactivate a staff account with safety checks.

        Args:
            db: Async database session.
            staff_id: Staff UUID to deactivate.
            current_staff: Authenticated staff performing the action.

        Returns:
            The deactivated Staff model.

        Raises:
            StaffNotFoundException: If the staff account does not exist.
            HTTPException: If targeting the default admin or the caller's own account.
        """
        try:
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
            await db.commit()
            await db.refresh(staff)
        except Exception:
            await db.rollback()
            raise
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
        """Reactivate a previously deactivated staff account.

        Args:
            db: Async database session.
            staff_id: Staff UUID to restore.
            current_staff: Authenticated staff performing the action.

        Returns:
            The restored Staff model.

        Raises:
            StaffNotFoundException: If no staff account exists for the given id.
        """
        try:
            staff = await StaffRepository.get_by_id(db, staff_id, include_inactive=True)
            if staff is None:
                raise StaffNotFoundException()

            staff = await StaffRepository.restore(db, staff)
            await db.commit()
            await db.refresh(staff)
        except Exception:
            await db.rollback()
            raise
        library_api.info(
            "Staff restored: %s by %s",
            staff.email,
            current_staff.email,
        )
        return staff
