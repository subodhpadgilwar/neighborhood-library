"""Pydantic schemas for lending operations. LendingResponse includes computed is_overdue field."""

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.core.timezone import now_utc, to_local, to_utc

LendingStatusFilter = Literal["active", "returned", "overdue"]
LendingSortBy = Literal["borrowed_at", "due_date", "member_name", "book_title", "returned_at"]
LendingSortOrder = Literal["asc", "desc"]


class BorrowRequest(BaseModel):
    """Schema for initiating a book loan."""

    book_id: UUID
    member_id: UUID
    due_date: Optional[datetime] = None


class ReturnRequest(BaseModel):
    """Schema for marking a loan as returned."""

    lending_id: UUID


class LendingFilterParams(BaseModel):
    """Query parameters for filtering and paginating lending history."""

    status: Optional[LendingStatusFilter] = None
    member_name: Optional[str] = None
    book_title: Optional[str] = None
    borrowed_from: Optional[datetime] = None
    borrowed_to: Optional[datetime] = None
    sort_by: Optional[LendingSortBy] = "borrowed_at"
    sort_order: Optional[LendingSortOrder] = "desc"
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)


class LendingHistoryResponse(BaseModel):
    """Paginated lending history response."""

    items: list["LendingResponse"]
    total: int
    page: int
    limit: int
    total_pages: int


class ActiveLoansResponse(BaseModel):
    """Paginated active loans response."""

    items: list["LendingResponse"]
    total: int
    skip: int
    limit: int


class OverdueLoansResponse(BaseModel):
    """Paginated overdue loans response."""

    items: list["LendingResponse"]
    total: int
    skip: int
    limit: int


class UpdateDueDateRequest(BaseModel):
    """Schema for updating an active loan's due date."""

    due_date: datetime

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, value: datetime) -> datetime:
        """Ensure the due date is in the future.

        Args:
            value: Proposed due date.

        Returns:
            The validated due date.

        Raises:
            ValueError: If the due date is in the past or present.
        """
        if to_utc(value) <= now_utc():
            raise ValueError("Due date cannot be set in the past")
        return value


class LendingResponse(BaseModel):
    """Schema for lending API responses with related book/member details.

    Includes a computed ``is_overdue`` field derived from due_date and returned_at.
    """

    id: UUID
    borrowed_at: datetime
    due_date: datetime
    returned_at: Optional[datetime] = None

    book: Any = Field(default=None, exclude=True, repr=False)
    member: Any = Field(default=None, exclude=True, repr=False)
    created_by_staff: Any = Field(default=None, exclude=True, repr=False)

    model_config = ConfigDict(from_attributes=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def book_title(self) -> str | None:
        """Title of the borrowed book."""
        book = getattr(self, "book", None)
        if book is None:
            return None
        return getattr(book, "title", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def book_author(self) -> str | None:
        """Author of the borrowed book."""
        book = getattr(self, "book", None)
        if book is None:
            return None
        return getattr(book, "author", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def book_shelf_location(self) -> str | None:
        """Shelf location of the borrowed book."""
        book = getattr(self, "book", None)
        if book is None:
            return None
        return getattr(book, "shelf_location", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def member_name(self) -> str | None:
        """Name of the borrowing member."""
        member = getattr(self, "member", None)
        if member is None:
            return None
        return getattr(member, "name", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def member_email(self) -> str | None:
        """Email of the borrowing member."""
        member = getattr(self, "member", None)
        if member is None:
            return None
        return getattr(member, "email", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def processed_by(self) -> str | None:
        """Full name of the staff member who processed the loan."""
        staff = getattr(self, "created_by_staff", None)
        if staff is None:
            return None
        return getattr(staff, "full_name", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_overdue(self) -> bool:
        """Whether the loan is past its due date and not yet returned."""
        if self.returned_at is not None:
            return False
        return now_utc() > to_utc(self.due_date)

    def model_post_init(self, __context: object) -> None:
        """Convert UTC timestamps to the application local timezone."""
        self.borrowed_at = to_local(self.borrowed_at)  # type: ignore[misc]
        self.due_date = to_local(self.due_date)  # type: ignore[misc]
        self.returned_at = to_local(self.returned_at)  # type: ignore[misc]


LendingHistoryResponse.model_rebuild()
ActiveLoansResponse.model_rebuild()
OverdueLoansResponse.model_rebuild()
