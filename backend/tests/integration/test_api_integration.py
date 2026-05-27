"""API integration tests against a real PostgreSQL database."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyBorrowedException, BookNotAvailableException
from app.core.security import hash_password
from app.models.book import Book
from app.models.member import Member
from app.models.staff import Staff
from app.services.lending_service import LendingService

pytestmark = pytest.mark.integration

ADMIN_EMAIL = "integration-admin@example.com"
ADMIN_PASSWORD = "IntegrationTest1!"
STAFF_EMAIL = "integration-staff@example.com"
STAFF_PASSWORD = "IntegrationStaff1!"


async def _seed_admin(db: AsyncSession) -> Staff:
    admin = Staff(
        email=ADMIN_EMAIL,
        full_name="Integration Admin",
        hashed_password=hash_password(ADMIN_PASSWORD),
        role="admin",
        is_active=True,
        is_default_admin=True,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


async def _seed_staff(db: AsyncSession) -> Staff:
    staff = Staff(
        email=STAFF_EMAIL,
        full_name="Integration Staff",
        hashed_password=hash_password(STAFF_PASSWORD),
        role="staff",
        is_active=True,
        is_default_admin=False,
    )
    db.add(staff)
    await db.commit()
    await db.refresh(staff)
    return staff


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "version" in payload


async def test_login_success_and_failure(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await _seed_admin(db_session)

    success = await client.post(
        "/api/v1/auth/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert success.status_code == 200
    assert success.json()["token_type"] == "bearer"
    assert success.json()["access_token"]

    failure = await client.post(
        "/api/v1/auth/login",
        data={"username": ADMIN_EMAIL, "password": "wrong-password"},
    )
    assert failure.status_code == 401
    assert failure.json()["message"] == "Invalid email or password"


async def test_admin_route_requires_admin_role(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await _seed_admin(db_session)
    staff = await _seed_staff(db_session)
    staff_token = await _login(client, STAFF_EMAIL, STAFF_PASSWORD)

    response = await client.post(
        "/api/v1/auth/register",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={
            "full_name": "New Staff",
            "email": "new-staff@example.com",
            "password": "StrongPass123",
            "role": "staff",
        },
    )
    assert response.status_code == 403
    assert response.json()["message"] == "Admin privileges are required for this action"

    admin_token = await _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    allowed = await client.post(
        "/api/v1/auth/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "full_name": "New Staff",
            "email": "new-staff@example.com",
            "password": "StrongPass123",
            "role": "staff",
        },
    )
    assert allowed.status_code == 201
    assert allowed.json()["email"] == "new-staff@example.com"


async def test_borrow_rejects_duplicate_active_loan(db_session: AsyncSession) -> None:
    admin = await _seed_admin(db_session)

    book = Book(
        id=uuid4(),
        title="Integration Book",
        author="Test Author",
        isbn="9780000000001",
        genre="Test",
        copies_total=1,
        copies_available=1,
        is_active=True,
        created_by=admin.id,
    )
    member = Member(
        id=uuid4(),
        name="Integration Member",
        email="member@example.com",
        created_by=admin.id,
    )
    db_session.add_all([book, member])
    await db_session.commit()

    await LendingService.borrow_book(
        db_session,
        book.id,
        member.id,
        admin.id,
    )

    with pytest.raises(AlreadyBorrowedException) as exc_info:
        await LendingService.borrow_book(
            db_session,
            book.id,
            member.id,
            admin.id,
        )
    assert exc_info.value.status_code == 400

    member_two = Member(
        id=uuid4(),
        name="Second Member",
        email="member-two@example.com",
        created_by=admin.id,
    )
    db_session.add(member_two)
    await db_session.commit()

    with pytest.raises(BookNotAvailableException):
        await LendingService.borrow_book(
            db_session,
            book.id,
            member_two.id,
            admin.id,
        )
