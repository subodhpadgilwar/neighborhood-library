"""Base model configuration and AuditMixin for all SQLAlchemy ORM models.

Provides the shared audit columns (timestamps, staff attribution, soft delete)
used by every domain model except Staff.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.timezone import now_utc
from app.database import Base

__all__ = ["Base", "AuditMixin"]


class AuditMixin:
    """Mixin that adds audit trail columns to ORM models.

    All models except Staff inherit from this mixin. Provides automatic
    timestamp tracking and staff attribution for every record change.

    Staff does not use this mixin to avoid circular self-referencing foreign
    keys (``created_by`` pointing back to the staff table).

    Attributes:
        created_at: UTC timestamp when the record was created.
        updated_at: UTC timestamp of the last update; auto-updated by SQLAlchemy
            on every change.
        created_by: UUID of the staff member who created the record.
        updated_by: UUID of the staff member who last updated the record.
        is_active: Soft-delete flag. ``False`` means deactivated, not hard
            deleted, preserving data integrity and lending history.
    """

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
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff.id"),
        nullable=True,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff.id"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
