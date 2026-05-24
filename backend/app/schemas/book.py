from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.timezone import to_local


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=255)
    isbn: Optional[str] = Field(default=None, pattern=r"^\d{13}$")
    genre: Optional[str] = Field(default=None, max_length=100)
    copies_total: int = Field(ge=1, le=1000)


class BookCreate(BookBase):
    @field_validator("title", "author", "genre", "isbn", mode="before")
    @classmethod
    def strip_non_empty_strings(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "":
                raise ValueError("must not be blank or whitespace only")
            return stripped
        return value


class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    author: Optional[str] = Field(default=None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(default=None, pattern=r"^\d{13}$")
    genre: Optional[str] = Field(default=None, max_length=100)
    copies_total: Optional[int] = Field(default=None, ge=1, le=1000)


class BookResponse(BookBase):
    id: UUID
    copies_available: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        self.created_at = to_local(self.created_at)  # type: ignore[misc]
        self.updated_at = to_local(self.updated_at)  # type: ignore[misc]
