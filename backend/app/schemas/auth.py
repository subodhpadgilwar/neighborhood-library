"""Pydantic schemas for authentication requests and responses."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """JSON login body schema (documentation; login uses form-urlencoded)."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT access token responses."""

    access_token: str
    token_type: str = "bearer"
