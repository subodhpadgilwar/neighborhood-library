from datetime import timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_current_staff, get_db, get_optional_staff
from app.core.timezone import now_utc
from app.main import app
from app.models.staff import Staff
from app.schemas.book import BookListResponse, BookResponse
from app.schemas.lending import LendingHistoryResponse, LendingResponse
from app.schemas.member import MemberListResponse, MemberResponse
from app.schemas.staff import StaffListResponse, StaffResponse
from app.services.book_service import BookService
from app.services.lending_service import LendingService
from app.services.member_service import MemberService
from app.services.staff_service import StaffService


async def override_db():
    yield object()


def make_staff() -> Staff:
    return Staff(
        id=uuid4(),
        email="staff@example.com",
        full_name="Staff User",
        hashed_password="hashed",
        role="staff",
        is_active=True,
        is_default_admin=False,
        created_at=now_utc(),
        updated_at=now_utc(),
    )


def make_book_response(**overrides) -> BookResponse:
    data = {
        "id": uuid4(),
        "title": "Clean Architecture",
        "author": "Robert C. Martin",
        "isbn": "9780134494166",
        "genre": "Technology",
        "shelf_location": "A1",
        "copies_total": 2,
        "copies_available": 2,
        "is_active": True,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
    data.update(overrides)
    return BookResponse.model_validate(data)


def make_member_response(**overrides) -> MemberResponse:
    data = {
        "id": uuid4(),
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "9876543210",
        "address": "1 Library Street",
        "is_active": True,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
    data.update(overrides)
    return MemberResponse.model_validate(data)


def make_lending_response(**overrides) -> LendingResponse:
    data = {
        "id": uuid4(),
        "borrowed_at": now_utc(),
        "due_date": now_utc() + timedelta(days=14),
        "returned_at": None,
    }
    data.update(overrides)
    return LendingResponse.model_validate(data)


def make_staff_response(**overrides) -> StaffResponse:
    data = {
        "id": uuid4(),
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "admin",
        "is_active": True,
        "is_default_admin": True,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
    data.update(overrides)
    return StaffResponse.model_validate(data)


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_list_books_forwards_pagination_and_search(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def get_page(_db, **kwargs):
        captured.update(kwargs)
        book = make_book_response(title="Domain-Driven Design")
        return BookListResponse(
            items=[book],
            total=1,
            page=2,
            limit=5,
            total_pages=1,
        )

    monkeypatch.setattr(BookService, "get_page", get_page)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_optional_staff] = lambda: make_staff()

    try:
        response = TestClient(app).get(
            "/api/v1/books/",
            params={
                "page": 2,
                "limit": 5,
                "search": "domain",
                "genre": "Technology",
                "sort_by": "author",
                "sort_order": "desc",
                "include_inactive": True,
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert response.json()["items"][0]["title"] == "Domain-Driven Design"
    assert captured == {
        "page": 2,
        "limit": 5,
        "search": "domain",
        "genre": "Technology",
        "sort_by": "author",
        "sort_order": "desc",
        "include_inactive": True,
    }


def test_list_staff_forwards_pagination_and_sort(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def get_page(_db, **kwargs):
        captured.update(kwargs)
        staff = make_staff_response(full_name="Jane Admin", email="jane@example.com")
        return StaffListResponse(
            items=[staff],
            total=1,
            page=3,
            limit=25,
            total_pages=7,
        )

    monkeypatch.setattr(StaffService, "get_page", get_page)
    app.dependency_overrides[get_db] = override_db
    admin_staff = make_staff()
    admin_staff.role = "admin"
    admin_staff.is_default_admin = True
    app.dependency_overrides[get_current_staff] = lambda: admin_staff

    try:
        response = TestClient(app).get(
            "/api/v1/staff/",
            params={
                "page": 3,
                "limit": 25,
                "include_inactive": True,
                "sort_by": "email",
                "sort_order": "desc",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    assert response.json()["items"][0]["email"] == "jane@example.com"
    assert captured == {
        "page": 3,
        "limit": 25,
        "include_inactive": True,
        "sort_by": "email",
        "sort_order": "desc",
    }


def test_create_book_uses_authenticated_staff_id(monkeypatch) -> None:
    staff = make_staff()
    captured: dict[str, object] = {}

    async def create(_db, data, staff_id: UUID):
        captured["staff_id"] = staff_id
        captured["title"] = data.title
        return make_book_response(title=data.title, copies_total=data.copies_total)

    monkeypatch.setattr(BookService, "create", create)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_staff] = lambda: staff

    try:
        response = TestClient(app).post(
            "/api/v1/books/",
            json={
                "title": "Refactoring",
                "author": "Martin Fowler",
                "isbn": "9780201485677",
                "genre": "Technology",
                "copies_total": 3,
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 201
    assert response.json()["title"] == "Refactoring"
    assert captured == {"staff_id": staff.id, "title": "Refactoring"}


def test_list_members_requires_authentication() -> None:
    app.dependency_overrides[get_db] = override_db

    try:
        response = TestClient(app).get("/api/v1/members/")
    finally:
        clear_overrides()

    assert response.status_code == 401


def test_create_member_normalizes_phone_and_uses_staff_id(monkeypatch) -> None:
    staff = make_staff()
    captured: dict[str, object] = {}

    async def create(_db, data, staff_id: UUID):
        captured["staff_id"] = staff_id
        captured["phone"] = data.phone
        return make_member_response(
            name=data.name,
            email=str(data.email),
            phone=data.phone,
        )

    monkeypatch.setattr(MemberService, "create", create)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_staff] = lambda: staff

    try:
        response = TestClient(app).post(
            "/api/v1/members/",
            json={
                "name": "Grace Hopper",
                "email": "grace@example.com",
                "phone": "(987) 654-3210",
                "address": "2 Library Street",
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 201
    assert response.json()["phone"] == "9876543210"
    assert captured == {"staff_id": staff.id, "phone": "9876543210"}


def test_borrow_book_passes_staff_and_due_date(monkeypatch) -> None:
    staff = make_staff()
    book_id = uuid4()
    member_id = uuid4()
    due_date = now_utc() + timedelta(days=7)
    captured: dict[str, object] = {}

    async def borrow_book(_db, passed_book_id, passed_member_id, staff_id, due_date=None):
        captured.update(
            {
                "book_id": passed_book_id,
                "member_id": passed_member_id,
                "staff_id": staff_id,
                "due_date": due_date,
            }
        )
        return make_lending_response(due_date=due_date)

    monkeypatch.setattr(LendingService, "borrow_book", borrow_book)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_staff] = lambda: staff

    try:
        response = TestClient(app).post(
            "/api/v1/lending/borrow",
            json={
                "book_id": str(book_id),
                "member_id": str(member_id),
                "due_date": due_date.isoformat(),
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 201
    assert response.json()["returned_at"] is None
    assert captured == {
        "book_id": book_id,
        "member_id": member_id,
        "staff_id": staff.id,
        "due_date": due_date,
    }


def test_lending_history_builds_filter_params(monkeypatch) -> None:
    staff = make_staff()
    captured: dict[str, object] = {}

    async def get_history(_db, filters):
        captured["filters"] = filters
        loan = make_lending_response()
        return LendingHistoryResponse(
            items=[loan],
            total=1,
            page=2,
            limit=10,
            total_pages=3,
        )

    monkeypatch.setattr(LendingService, "get_history", get_history)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_staff] = lambda: staff

    try:
        response = TestClient(app).get(
            "/api/v1/lending/history",
            params={
                "status": "active",
                "member_name": "ada",
                "book_title": "clean",
                "sort_by": "due_date",
                "sort_order": "asc",
                "skip": 10,
                "limit": 10,
            },
        )
    finally:
        clear_overrides()

    filters = captured["filters"]
    assert response.status_code == 200
    assert response.json()["page"] == 2
    assert filters.status == "active"
    assert filters.member_name == "ada"
    assert filters.book_title == "clean"
    assert filters.sort_by == "due_date"
    assert filters.sort_order == "asc"
    assert filters.skip == 10
    assert filters.limit == 10


def test_update_due_date_rejects_past_due_date() -> None:
    staff = make_staff()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_staff] = lambda: staff

    try:
        response = TestClient(app).put(
            f"/api/v1/lending/{uuid4()}/due-date",
            json={"due_date": (now_utc() - timedelta(days=1)).isoformat()},
        )
    finally:
        clear_overrides()

    assert response.status_code == 422
