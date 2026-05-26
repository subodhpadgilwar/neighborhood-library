"""Member model representing registered library members who can borrow books.

Maps to the ``members`` table. Email is unique alongside the UUID primary key.
"""

import uuid
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.lending import LendingRecord
    from app.models.staff import Staff


class Member(Base, AuditMixin):
    """Represents a library member who can borrow books.

    Email is unique and used as a natural identifier alongside the UUID primary
    key for lookups and duplicate detection.

    Attributes:
        id: Primary key UUID.
        name: Member display name.
        email: Unique contact email.
        phone: Optional phone number (normalized in Pydantic schemas).
        address: Optional mailing address.
        created_by_staff: ORM relationship to creating staff.
        updated_by_staff: ORM relationship to last updating staff.
        lending_records: All loans associated with this member.
    """

    __tablename__ = "members"
    __table_args__ = (Index("ix_members_name", "name"),)

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
