import uuid
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.lending import LendingRecord
    from app.models.staff import Staff


class Member(Base, AuditMixin):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_by_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff",
        foreign_keys="Member.created_by",
        primaryjoin="Member.created_by == Staff.id",
    )
    updated_by_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff",
        foreign_keys="Member.updated_by",
        primaryjoin="Member.updated_by == Staff.id",
    )
    lending_records: Mapped[list["LendingRecord"]] = relationship(
        back_populates="member",
    )
