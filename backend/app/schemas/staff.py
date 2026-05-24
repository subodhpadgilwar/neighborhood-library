import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.timezone import to_local


def _validate_password_strength(password: str) -> str:
    if not re.search(r"[A-Z]", password):
        raise ValueError("password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("password must contain at least one digit")
    return password


class StaffBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr


class StaffCreate(StaffBase):
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_password_strength(value)


class StaffUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return _validate_password_strength(value)

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("new_password and confirm_password must match")
        return self


class AdminChangePasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return _validate_password_strength(value)

    @model_validator(mode="after")
    def passwords_match(self) -> "AdminChangePasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("new_password and confirm_password must match")
        return self


class StaffResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_default_admin: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: object) -> None:
        self.created_at = to_local(self.created_at)  # type: ignore[misc]
        self.updated_at = to_local(self.updated_at)  # type: ignore[misc]
