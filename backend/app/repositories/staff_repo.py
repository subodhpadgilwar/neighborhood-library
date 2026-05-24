from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.core.logger import library_api
from app.core.security import hash_password
from app.core.timezone import now_utc
from app.models.staff import Staff
from app.schemas.staff import StaffCreate, StaffUpdate


class StaffRepository:
    @staticmethod
    def _select_staff() -> Select[tuple[Staff]]:
        return select(Staff)

    @staticmethod
    def _apply_active_filter(
        stmt: Select[tuple[Staff]],
        include_inactive: bool,
    ) -> Select[tuple[Staff]]:
        if not include_inactive:
            stmt = stmt.where(Staff.is_active.is_(True))
        return stmt

    @staticmethod
    async def get_all(
        db: AsyncSession,
        include_inactive: bool = False,
    ) -> list[Staff]:
        library_api.debug(
            "StaffRepository.get_all include_inactive=%s",
            include_inactive,
        )
        stmt = StaffRepository._apply_active_filter(
            StaffRepository._select_staff(),
            include_inactive,
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        staff_id: UUID,
        include_inactive: bool = False,
    ) -> Staff | None:
        library_api.debug(
            "StaffRepository.get_by_id staff_id=%s include_inactive=%s",
            staff_id,
            include_inactive,
        )
        stmt = StaffRepository._apply_active_filter(
            StaffRepository._select_staff().where(Staff.id == staff_id),
            include_inactive,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Staff | None:
        library_api.debug("StaffRepository.get_by_email email=%s", email)
        result = await db.execute(
            StaffRepository._select_staff().where(Staff.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: StaffCreate) -> Staff:
        library_api.debug("StaffRepository.create email=%s", data.email)
        staff = Staff(
            email=str(data.email),
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        db.add(staff)
        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def update(db: AsyncSession, staff: Staff, data: StaffUpdate) -> Staff:
        library_api.debug("StaffRepository.update staff_id=%s", staff.id)
        updates = data.model_dump(exclude_none=True)
        if "email" in updates and updates["email"] is not None:
            updates["email"] = str(updates["email"])
        for field, value in updates.items():
            setattr(staff, field, value)
        staff.updated_at = now_utc()
        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def update_password(db: AsyncSession, staff: Staff, new_password: str) -> Staff:
        library_api.debug("StaffRepository.update_password staff_id=%s", staff.id)
        staff.hashed_password = hash_password(new_password)
        staff.updated_at = now_utc()
        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def soft_delete(db: AsyncSession, staff: Staff) -> Staff:
        library_api.debug("StaffRepository.soft_delete staff_id=%s", staff.id)
        staff.is_active = False
        staff.updated_at = now_utc()
        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def restore(db: AsyncSession, staff: Staff) -> Staff:
        library_api.debug("StaffRepository.restore staff_id=%s", staff.id)
        staff.is_active = True
        staff.updated_at = now_utc()
        await db.commit()
        await db.refresh(staff)
        return staff
