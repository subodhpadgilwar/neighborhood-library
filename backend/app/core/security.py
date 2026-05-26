"""Security utilities for JWT authentication and password hashing using bcrypt.

Provides password hashing/verification and JWT creation/decoding used by the
auth service and ``get_current_staff`` dependency.
"""

import hashlib
from datetime import timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.logger import library_api
from app.core.timezone import now_utc

# bcrypt only uses the first 72 bytes; pre-hash longer passwords for consistency.
_BCRYPT_MAX_BYTES = 72

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _prepare_password(password: str) -> str:
    """Normalize passwords so bcrypt never rejects inputs over 72 bytes.

    Args:
        password: Plain-text password from the client.

    Returns:
        Original password or its SHA-256 hex digest when over 72 UTF-8 bytes.
    """
    encoded = password.encode("utf-8")
    if len(encoded) <= _BCRYPT_MAX_BYTES:
        return password
    return hashlib.sha256(encoded).hexdigest()


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Never store plain-text passwords in the database.

    Args:
        password: Plain-text password to hash.

    Returns:
        bcrypt hash string suitable for persistence.
    """
    return pwd_context.hash(_prepare_password(password))


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Uses timing-safe comparison via passlib.

    Args:
        plain: Plain-text password from login attempt.
        hashed: Stored bcrypt hash.

    Returns:
        True if the password matches the hash.
    """
    return pwd_context.verify(_prepare_password(plain), hashed)


def create_access_token(data: dict[str, Any]) -> str:
    """Create a signed JWT access token with an expiration claim.

    The token ``sub`` claim should contain the staff UUID string.

    Args:
        data: JWT payload fields (e.g. ``{"sub": staff_id}``).

    Returns:
        Encoded JWT string signed with ``SECRET_KEY``.
    """
    expire = now_utc() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {**data, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token.

    Returns None instead of raising on invalid or expired tokens so callers can
    handle authentication failures gracefully.

    Args:
        token: Bearer token string from the Authorization header.

    Returns:
        Decoded payload dict, or None if invalid, expired, or malformed.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        if not isinstance(payload, dict):
            library_api.warning("JWT decode returned non-dict payload")
            return None
        return payload
    except JWTError as exc:
        library_api.warning("JWT decode failed: %s", exc)
        return None
    except Exception as exc:
        library_api.warning("JWT decode failed with unexpected error: %s", exc)
        return None
