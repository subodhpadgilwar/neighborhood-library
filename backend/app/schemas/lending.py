from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field

from app.core.timezone import now_utc, to_local, to_utc


class BorrowRequest(BaseModel):
    book_id: UUID
    member_id: UUID


class ReturnRequest(BaseModel):
    lending_id: UUID


class LendingResponse(BaseModel):
    id: UUID
    book_id: UUID
    member_id: UUID
    borrowed_at: datetime
    due_date: datetime
    returned_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_overdue(self) -> bool:
        if self.returned_at is not None:
            return False
        return now_utc() > to_utc(self.due_date)

    def model_post_init(self, __context: Any) -> None:
        self.borrowed_at = to_local(self.borrowed_at)  # type: ignore[misc]
        self.due_date = to_local(self.due_date)  # type: ignore[misc]
        self.returned_at = to_local(self.returned_at)  # type: ignore[misc]
