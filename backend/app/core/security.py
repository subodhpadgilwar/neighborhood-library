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
    """Normalize passwords so bcrypt/passlib never reject inputs over 72 bytes."""
    encoded = password.encode("utf-8")
    if len(encoded) <= _BCRYPT_MAX_BYTES:
        return password
    return hashlib.sha256(encoded).hexdigest()


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return pwd_context.hash(_prepare_password(password))


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(_prepare_password(plain), hashed)


def create_access_token(data: dict[str, Any]) -> str:
    """Create a signed JWT access token with an expiration claim."""
    expire = now_utc() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {**data, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode a JWT access token. Returns None if invalid or expired."""
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
