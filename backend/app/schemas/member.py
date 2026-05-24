import re
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator

from app.core.timezone import to_local

PHONE_DIGITS_PATTERN = re.compile(r"^\d{10,15}$")


class MemberBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = Field(default=None, max_length=500)

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value: object) -> object:
        if value is None:
            return value
        if not isinstance(value, str):
            return value
        digits = re.sub(r"\D", "", value)
        if not PHONE_DIGITS_PATTERN.fullmatch(digits):
            raise ValueError("phone must contain 10 to 15 digits after removing formatting")
        return digits


class MemberCreate(MemberBase):
    @field_validator("name", "email", "phone", "address", mode="before")
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


class MemberUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = Field(default=None, max_length=500)

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value: object) -> object:
        return MemberBase.normalize_phone(value)


class MemberResponse(MemberBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    created_by_staff: Any = Field(default=None, exclude=True, repr=False)
    updated_by_staff: Any = Field(default=None, exclude=True, repr=False)

    model_config = ConfigDict(from_attributes=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def created_by(self) -> str | None:
        staff = getattr(self, "created_by_staff", None)
        if staff is None:
            return None
        return getattr(staff, "full_name", None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def updated_by(self) -> str | None:
        staff = getattr(self, "updated_by_staff", None)
        if staff is None:
            return None
        return getattr(staff, "full_name", None)

    def model_post_init(self, __context: object) -> None:
        self.created_at = to_local(self.created_at)  # type: ignore[misc]
        self.updated_at = to_local(self.updated_at)  # type: ignore[misc]
