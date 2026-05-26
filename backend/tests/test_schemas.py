from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.book import BookListResponse, BookResponse, BookUpdate
from app.schemas.lending import LendingFilterParams
from app.schemas.member import MemberListResponse, MemberResponse


def test_book_list_response_wraps_items_and_pagination_metadata() -> None:
    book = BookResponse.model_validate(
        {
            "id": uuid4(),
            "title": "Clean Architecture",
            "author": "Robert C. Martin",
            "isbn": "9780134494166",
            "genre": "Technology",
            "shelf_location": "A1",
            "copies_total": 2,
            "copies_available": 2,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    )

    response = BookListResponse(
        items=[book],
        total=1,
        page=1,
        limit=10,
        total_pages=1,
    )

    assert response.total == 1
    assert response.items[0].title == "Clean Architecture"


def test_member_list_response_wraps_items_and_pagination_metadata() -> None:
    member = MemberResponse.model_validate(
        {
            "id": uuid4(),
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "phone": "9876543210",
            "address": "1 Library Street",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    )

    response = MemberListResponse(
        items=[member],
        total=1,
        page=1,
        limit=10,
        total_pages=1,
    )

    assert response.total == 1
    assert response.items[0].email == "ada@example.com"


def test_lending_filters_reject_unsupported_sort_values() -> None:
    with pytest.raises(ValidationError):
        LendingFilterParams(sort_by="unsupported")


def test_book_update_rejects_invalid_copy_count() -> None:
    with pytest.raises(ValidationError):
        BookUpdate(copies_total=0)
