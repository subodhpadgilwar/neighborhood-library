from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.core.timezone import now_utc, to_local, to_utc

LendingStatusFilter = Literal["active", "returned", "overdue"]
LendingSortBy = Literal["borrowed_at", "due_date", "member_name", "book_title", "returned_at"]
LendingSortOrder = Literal["asc", "desc"]


class BorrowRequest(BaseModel):
    book_id: UUID
    member_id: UUID
    due_date: Optional[datetime] = None


class ReturnRequest(BaseModel):
    lending_id: UUID


class LendingFilterParams(BaseModel):
    status: Optional[LendingStatusFilter] = None
    member_name: Optional[str] = None
    book_title: Optional[str] = None
    borrowed_from: Optional[datetime] = None
    borrowed_to: Optional[datetime] = None
    sort_by: Optional[LendingSortBy] = "borrowed_at"
    sort_order: Optional[LendingSortOrder] = "desc"
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in ("active", "returned", "overdue"):
            raise ValueError("status must be one of: active, returned, overdue")
        return value

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, value: Optional[str]) -> Optional[str]:
        allowed = ("borrowed_at", "due_date", "member_name", "book_title", "returned_at")
        if value is not None and value not in allowed:
            raise ValueError(f"sort_by must be one of: {', '.join(allowed)}")
        return value

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in ("asc", "desc"):
            raise ValueError("sort_order must be one of: asc, desc")
        return value


class LendingHistoryResponse(BaseModel):
    items: list["LendingResponse"]
    total: int
    page: int
    limit: int
    total_pages: int


class UpdateDueDateRequest(BaseModel):
    due_date: datetime

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, value: datetime) -> datetime:
        if to_utc(value) <= now_utc():
            raise ValueError("Due date cannot be set in the past")
        return value


class LendingResponse(BaseModel):
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
        book = getattr(self, "book", None)
        if book is None:
            return None
        return getattr(book, "title", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def book_author(self) -> str | None:
        book = getattr(self, "book", None)
        if book is None:
            return None
        return getattr(book, "author", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def member_name(self) -> str | None:
        member = getattr(self, "member", None)
        if member is None:
            return None
        return getattr(member, "name", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def member_email(self) -> str | None:
        member = getattr(self, "member", None)
        if member is None:
            return None
        return getattr(member, "email", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def processed_by(self) -> str | None:
        staff = getattr(self, "created_by_staff", None)
        if staff is None:
            return None
        return getattr(staff, "full_name", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_overdue(self) -> bool:
        if self.returned_at is not None:
            return False
        return now_utc() > to_utc(self.due_date)

    def model_post_init(self, __context: object) -> None:
        self.borrowed_at = to_local(self.borrowed_at)  # type: ignore[misc]
        self.due_date = to_local(self.due_date)  # type: ignore[misc]
        self.returned_at = to_local(self.returned_at)  # type: ignore[misc]


LendingHistoryResponse.model_rebuild()
