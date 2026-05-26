from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_current_staff, get_db
from app.core.timezone import now_utc
from app.main import app
from app.models.staff import Staff
from app.services.staff_service import StaffService


def make_staff(role: str = "staff") -> Staff:
    return Staff(
        id=uuid4(),
        email=f"{role}-{uuid4()}@example.com",
        full_name=f"{role.title()} User",
        hashed_password="hashed",
        role=role,
        is_default_admin=role == "admin",
        is_active=True,
        created_at=now_utc(),
        updated_at=now_utc(),
    )


async def override_db():
    yield object()


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_non_admin_cannot_list_staff() -> None:
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_staff] = lambda: make_staff("staff")

    try:
        response = TestClient(app).get("/api/v1/staff/")
    finally:
        clear_overrides()

    assert response.status_code == 403
    assert response.json()["message"] == "Admin privileges are required for this action"


def test_non_admin_cannot_register_staff() -> None:
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_staff] = lambda: make_staff("staff")

    try:
        response = TestClient(app).post(
            "/api/v1/auth/register",
            json={
                "full_name": "New Staff",
                "email": "new.staff@example.com",
                "password": "StrongPass1",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 403
    assert response.json()["message"] == "Admin privileges are required for this action"


def test_staff_can_change_own_password(monkeypatch) -> None:
    current_staff = make_staff("staff")

    async def change_own_password(_db, staff, _data):
        assert staff is current_staff
        return staff

    monkeypatch.setattr(StaffService, "change_own_password", change_own_password)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_staff] = lambda: current_staff

    try:
        response = TestClient(app).put(
            "/api/v1/staff/me/change-password",
            json={
                "current_password": "OldPass1",
                "new_password": "NewPass1",
                "confirm_password": "NewPass1",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert response.json()["id"] == str(current_staff.id)
    assert response.json()["role"] == "staff"
