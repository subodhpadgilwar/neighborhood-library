"""Pydantic schemas for staff management including password validation."""

import re
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.timezone import to_local

StaffRole = Literal["admin", "staff"]


def _validate_password_strength(password: str) -> str:
    """Validate that a password meets minimum complexity requirements.

    Args:
        password: Plain-text password to validate.

    Returns:
        The password unchanged if valid.

    Raises:
        ValueError: If the password lacks an uppercase letter, lowercase letter, or digit.
    """
    if not re.search(r"[A-Z]", password):
        raise ValueError("password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("password must contain at least one digit")
    return password


class StaffBase(BaseModel):
    """Shared staff profile fields."""

    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr


class StaffCreate(StaffBase):
    """Schema for creating a new staff account with password."""

    password: str = Field(min_length=8)
    role: StaffRole = "staff"

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Validate password strength for new staff accounts.

        Args:
            value: Plain-text password.

        Returns:
            The validated password.

        Raises:
            ValueError: If the password does not meet complexity requirements.
        """
        return _validate_password_strength(value)


class StaffUpdate(BaseModel):
    """Schema for partial staff profile updates; all fields are optional."""

    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[StaffRole] = None


class ChangePasswordRequest(BaseModel):
    """Schema for a staff member changing their own password."""

    current_password: str
    new_password: str = Field(min_length=8)
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        """Validate new password strength.

        Args:
            value: Plain-text new password.

        Returns:
            The validated password.

        Raises:
            ValueError: If the password does not meet complexity requirements.
        """
        return _validate_password_strength(value)

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        """Ensure new_password and confirm_password match.

        Returns:
            This model instance.

        Raises:
            ValueError: If new_password and confirm_password differ.
        """
        if self.new_password != self.confirm_password:
            raise ValueError("new_password and confirm_password must match")
        return self


class AdminChangePasswordRequest(BaseModel):
    """Schema for an admin resetting another staff member's password."""

    new_password: str = Field(min_length=8)
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        """Validate new password strength.

        Args:
            value: Plain-text new password.

        Returns:
            The validated password.

        Raises:
            ValueError: If the password does not meet complexity requirements.
        """
        return _validate_password_strength(value)

    @model_validator(mode="after")
    def passwords_match(self) -> "AdminChangePasswordRequest":
        """Ensure new_password and confirm_password match.

        Returns:
            This model instance.

        Raises:
            ValueError: If new_password and confirm_password differ.
        """
        if self.new_password != self.confirm_password:
            raise ValueError("new_password and confirm_password must match")
        return self


class StaffResponse(BaseModel):
    """Schema for staff API responses with local timestamps."""

    id: UUID
    email: EmailStr
    full_name: str
    role: StaffRole
    is_active: bool
    is_default_admin: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: object) -> None:
        """Convert UTC timestamps to the application local timezone."""
        self.created_at = to_local(self.created_at)  # type: ignore[misc]
        self.updated_at = to_local(self.updated_at)  # type: ignore[misc]
