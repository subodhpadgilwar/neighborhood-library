"""Book model representing physical books in the library collection.

Maps to the ``books`` table. Tracks copy counts for O(1) availability checks.
"""

import uuid
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import CheckConstraint, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.lending import LendingRecord
    from app.models.staff import Staff


class Book(Base, AuditMixin):
    """Represents a book title in the library catalog.

    ``copies_total`` is the permanent count of physical copies owned.
    ``copies_available`` decrements on borrow and increments on return, enabling
    O(1) availability checks without expensive ``COUNT`` queries on lending
    records.

    Database constraints ensure ``copies_available`` never goes negative and
    ``copies_total`` is always at least 1.

    Attributes:
        id: Primary key UUID.
        title: Book title.
        author: Author name.
        isbn: Optional 13-digit ISBN (unique when set).
        genre: Optional genre label.
        shelf_location: Optional shelf identifier for staff retrieval.
        copies_total: Total physical copies owned.
        copies_available: Copies currently available to borrow.
        created_by_staff: ORM relationship to creating staff (loaded on demand).
        updated_by_staff: ORM relationship to last updating staff.
        lending_records: All lending transactions for this book.
    """

    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("copies_available >= 0", name="ck_books_copies_available_nonneg"),
        CheckConstraint("copies_total >= 1", name="ck_books_copies_total_min"),
        CheckConstraint(
            "copies_available <= copies_total",
            name="ck_books_copies_available_lte_total",
        ),
        Index("ix_books_title", "title"),
        Index("ix_books_author", "author"),
        Index("ix_books_genre", "genre"),
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
    shelf_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
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
