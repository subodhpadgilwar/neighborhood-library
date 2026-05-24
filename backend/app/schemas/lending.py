from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.timezone import now_utc, to_local, to_utc


class BorrowRequest(BaseModel):
    book_id: UUID
    member_id: UUID


class ReturnRequest(BaseModel):
    lending_id: UUID


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
