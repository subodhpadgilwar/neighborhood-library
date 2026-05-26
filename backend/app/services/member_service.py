"""Service layer for member business logic.

Orchestrates between repository layer and API layer. All business rules and
validation that requires database context live here.
"""

import math
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateEmailException, MemberNotFoundException
from app.core.logger import library_api
from app.models.member import Member
from app.repositories.lending_repo import LendingRepository
from app.repositories.member_repo import MemberRepository
from app.schemas.member import MemberCreate, MemberListResponse, MemberResponse, MemberUpdate


class MemberService:
    """Business logic for library member (patron) operations."""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: str | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> list[Member]:
        """Return a paginated list of members.

        Args:
            db: Async database session.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            include_inactive: When True, include soft-deleted members.

        Returns:
            List of Member models.
        """
        return await MemberRepository.get_all(
            db,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    @staticmethod
    async def get_page(
        db: AsyncSession,
        page: int = 1,
        limit: int = 100,
        include_inactive: bool = False,
        search: str | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> MemberListResponse:
        """Return a paginated, filterable member response."""
        skip = (page - 1) * limit
        members = await MemberRepository.get_all(
            db,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total = await MemberRepository.count(
            db,
            include_inactive=include_inactive,
            search=search,
        )
        return MemberListResponse(
            items=[MemberResponse.model_validate(member) for member in members],
            total=total,
            page=page,
            limit=limit,
            total_pages=math.ceil(total / limit) if limit > 0 else 0,
        )

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        member_id: UUID,
        include_inactive: bool = False,
    ) -> Member:
        """Fetch a single member by primary key.

        Args:
            db: Async database session.
            member_id: Member UUID.
            include_inactive: When True, allow loading a soft-deleted member.

        Returns:
            The Member model.

        Raises:
            MemberNotFoundException: If no member exists for the given id.
        """
        member = await MemberRepository.get_by_id(
            db,
            member_id,
            include_inactive=include_inactive,
        )
        if member is None:
            raise MemberNotFoundException(member_id)
        return member

    @staticmethod
    async def create(db: AsyncSession, data: MemberCreate, staff_id: UUID) -> Member:
        """Register a new library member.

        Args:
            db: Async database session.
            data: Member creation payload.
            staff_id: UUID of the staff member performing the action.

        Returns:
            The persisted Member model.

        Raises:
            DuplicateEmailException: If the email is already registered.
        """
        email = str(data.email)
        try:
            existing = await MemberRepository.get_by_email(db, email)
            if existing is not None:
                raise DuplicateEmailException(email)

            member = await MemberRepository.create(db, data)
            member.created_by = staff_id
            member_id = member.id
            await db.commit()
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateEmailException(email) from exc
        except Exception:
            await db.rollback()
            raise

        loaded = await MemberRepository.get_by_id(db, member_id, include_inactive=True)
        member = loaded if loaded is not None else member
        library_api.info("Member registered: %s", member.email)
        return member

    @staticmethod
    async def update(
        db: AsyncSession,
        member_id: UUID,
        data: MemberUpdate,
        staff_id: UUID,
    ) -> Member:
        """Update an existing member's fields.

        Args:
            db: Async database session.
            member_id: Member UUID to update.
            data: Partial update payload.
            staff_id: UUID of the staff member performing the action.

        Returns:
            The updated Member model.

        Raises:
            MemberNotFoundException: If the member does not exist.
            DuplicateEmailException: If the new email belongs to another member.
        """
        try:
            member = await MemberRepository.get_by_id(db, member_id)
            if member is None:
                raise MemberNotFoundException(member_id)

            if data.email is not None:
                new_email = str(data.email)
                if new_email != member.email:
                    existing = await MemberRepository.get_by_email(db, new_email)
                    if existing is not None:
                        raise DuplicateEmailException(new_email)

            member.updated_by = staff_id
            member = await MemberRepository.update(db, member, data)
            updated_id = member.id
            await db.commit()
        except IntegrityError as exc:
            await db.rollback()
            if data.email is not None:
                raise DuplicateEmailException(str(data.email)) from exc
            raise
        except Exception:
            await db.rollback()
            raise

        loaded = await MemberRepository.get_by_id(db, updated_id, include_inactive=True)
        return loaded if loaded is not None else member

    @staticmethod
    async def soft_delete(db: AsyncSession, member_id: UUID, staff_id: UUID) -> Member:
        """Soft-delete a member when they have no active loans.

        Args:
            db: Async database session.
            member_id: Member UUID to deactivate.
            staff_id: UUID of the staff member performing the action.

        Returns:
            The deactivated Member model.

        Raises:
            MemberNotFoundException: If the member does not exist or is already inactive.
            HTTPException: If the member still has active loan(s).
        """
        try:
            member = await MemberRepository.get_by_id(
                db,
                member_id,
                include_inactive=False,
            )
            if member is None:
                raise MemberNotFoundException(member_id)

            active_loans = await LendingRepository.get_active_by_member(db, member_id)
            if active_loans:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete member with {len(active_loans)} active loan(s)",
                )

            member = await MemberRepository.soft_delete(db, member, staff_id)
            updated_id = member.id
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        loaded = await MemberRepository.get_by_id(db, updated_id, include_inactive=True)
        member = loaded if loaded is not None else member
        library_api.info("Member soft deleted: %s", member_id)
        return member

    @staticmethod
    async def restore(db: AsyncSession, member_id: UUID, staff_id: UUID) -> Member:
        """Reactivate a previously soft-deleted member.

        Args:
            db: Async database session.
            member_id: Member UUID to restore.
            staff_id: UUID of the staff member performing the action.

        Returns:
            The restored Member model.

        Raises:
            MemberNotFoundException: If no member exists for the given id.
        """
        try:
            member = await MemberRepository.get_by_id(
                db,
                member_id,
                include_inactive=True,
            )
            if member is None:
                raise MemberNotFoundException(member_id)

            member = await MemberRepository.restore(db, member, staff_id)
            updated_id = member.id
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        loaded = await MemberRepository.get_by_id(db, updated_id, include_inactive=True)
        member = loaded if loaded is not None else member
        library_api.info("Member restored: %s", member_id)
        return member
