"""Staff model representing library employees who manage the system.

Maps to the ``staff`` table. Staff authenticate via JWT and process loans,
catalog changes, and member management.
"""

import uuid
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.timezone import now_utc
from app.database import Base


class Staff(Base):
    """Represents a library staff member who can log in and manage the system.

    Intentionally does not inherit ``AuditMixin`` to avoid self-referencing
    foreign keys (``created_by`` on staff would point back to staff and cause
    circular dependency issues with SQLAlchemy relationship loading).

    The ``is_default_admin`` flag identifies the auto-created admin from
    environment variables. The default admin cannot be deactivated to prevent
    system lockout.

    Attributes:
        id: Primary key UUID.
        email: Unique login email (OAuth2 username).
        hashed_password: bcrypt password hash.
        full_name: Display name for UI and audit trails.
        role: Authorization role (``admin`` or ``staff``).
        is_default_admin: True for the seeded admin account.
        is_active: Soft-delete flag for staff accounts.
        created_at: UTC timestamp when the account was created.
        updated_at: UTC timestamp of the last profile change.
    """

    __tablename__ = "staff"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="staff", nullable=False)
    is_default_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc,
        onupdate=now_utc,
        nullable=False,
    )
