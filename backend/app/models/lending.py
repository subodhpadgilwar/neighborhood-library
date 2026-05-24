import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.timezone import now_utc
from app.database import Base
from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.member import Member
    from app.models.staff import Staff


class LendingRecord(Base, AuditMixin):
    __tablename__ = "lending_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id"),
        nullable=False,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id"),
        nullable=False,
    )
    borrowed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc,
        nullable=False,
    )
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    book: Mapped["Book"] = relationship(back_populates="lending_records")
    member: Mapped["Member"] = relationship(back_populates="lending_records")
    created_by_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff",
        foreign_keys="LendingRecord.created_by",
        primaryjoin="LendingRecord.created_by == Staff.id",
    )
    updated_by_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff",
        foreign_keys="LendingRecord.updated_by",
        primaryjoin="LendingRecord.updated_by == Staff.id",
    )
