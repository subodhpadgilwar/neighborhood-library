import uuid
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.lending import LendingRecord
    from app.models.staff import Staff


class Book(Base, AuditMixin):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("copies_available >= 0", name="ck_books_copies_available_nonneg"),
        CheckConstraint("copies_total >= 1", name="ck_books_copies_total_min"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    isbn: Mapped[str | None] = mapped_column(String(13), unique=True, nullable=True, index=True)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    copies_total: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    copies_available: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_by_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff",
        foreign_keys="Book.created_by",
        primaryjoin="Book.created_by == Staff.id",
    )
    updated_by_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff",
        foreign_keys="Book.updated_by",
        primaryjoin="Book.updated_by == Staff.id",
    )
    lending_records: Mapped[list["LendingRecord"]] = relationship(
        back_populates="book",
    )
