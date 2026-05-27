"""Shared pytest helpers for unit and integration tests."""

from datetime import timedelta
from uuid import UUID, uuid4

from app.core.timezone import now_utc
from app.models.staff import Staff


def make_staff(*, role: str = "staff", staff_id: UUID | None = None) -> Staff:
    """Build an in-memory staff model for dependency overrides."""
    return Staff(
        id=staff_id or uuid4(),
        email="staff@example.com",
        full_name="Staff User",
        hashed_password="hashed",
        role=role,
        is_active=True,
        is_default_admin=False,
        created_at=now_utc(),
        updated_at=now_utc(),
    )


def clear_dependency_overrides(app) -> None:
    """Remove all FastAPI dependency overrides from the app."""
    app.dependency_overrides.clear()
