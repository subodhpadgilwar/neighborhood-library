"""Pydantic schemas for authentication requests and responses."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for staff login credentials."""

    email: EmailStr
    password: str = Field(min_length=6)


class TokenResponse(BaseModel):
    """Schema for JWT access token responses."""

    access_token: str
    token_type: str = "bearer"
