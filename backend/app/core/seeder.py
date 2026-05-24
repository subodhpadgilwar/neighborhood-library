"""Database seeders that run on application startup.

All seeders are idempotent — safe to run multiple times without creating
duplicate records.
"""

from typing import TypedDict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logger import library_api
from app.core.security import hash_password
from app.models.book import Book
from app.models.staff import Staff
from app.services.auth_service import get_staff_by_email


class SampleBookData(TypedDict):
    """Shape of each entry in ``SAMPLE_BOOKS`` for type checking."""

    title: str
    author: str
    isbn: str
    genre: str
    copies_total: int
    copies_available: int


SAMPLE_BOOKS: list[SampleBookData] = [
    {
        "title": "The Alchemist",
        "author": "Paulo Coelho",
        "isbn": "9780062315007",
        "genre": "Fiction",
        "copies_total": 3,
        "copies_available": 3,
    },
    {
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "isbn": "9780061935466",
        "genre": "Classic",
        "copies_total": 2,
        "copies_available": 2,
    },
    {
        "title": "1984",
        "author": "George Orwell",
        "isbn": "9780451524935",
        "genre": "Dystopian",
        "copies_total": 4,
        "copies_available": 4,
    },
    {
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "isbn": "9780743273565",
        "genre": "Classic",
        "copies_total": 2,
        "copies_available": 2,
    },
    {
        "title": "Sapiens",
        "author": "Yuval Noah Harari",
        "isbn": "9780062316097",
        "genre": "Non-Fiction",
        "copies_total": 3,
        "copies_available": 3,
    },
    {
        "title": "Atomic Habits",
        "author": "James Clear",
        "isbn": "9780735211292",
        "genre": "Self-Help",
        "copies_total": 3,
        "copies_available": 3,
    },
    {
        "title": "The Pragmatic Programmer",
        "author": "Andrew Hunt",
        "isbn": "9780135957059",
        "genre": "Technology",
        "copies_total": 2,
        "copies_available": 2,
    },
    {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "isbn": "9780132350884",
        "genre": "Technology",
        "copies_total": 2,
        "copies_available": 2,
    },
    {
        "title": "The Midnight Library",
        "author": "Matt Haig",
        "isbn": "9780525559474",
        "genre": "Fiction",
        "copies_total": 3,
        "copies_available": 3,
    },
    {
        "title": "Dune",
        "author": "Frank Herbert",
        "isbn": "9780441013593",
        "genre": "Science Fiction",
        "copies_total": 2,
        "copies_available": 2,
    },
]


async def seed_default_admin(db: AsyncSession) -> Staff | None:
    """Create the default admin staff from environment variables if none exists yet.

    Idempotent: checks by email before creating so restarting the app never
    duplicates the admin account.

    Args:
        db: Async database session.

    Returns:
        Existing or newly created ``Staff`` record, or None if seeding failed.
    """
    try:
        admin_email = str(settings.admin_email)
        existing = await get_staff_by_email(db, admin_email)
        if existing is not None:
            library_api.info("Default admin exists, skipping")
            return existing

        staff = Staff(
            email=admin_email,
            hashed_password=hash_password(settings.admin_password),
            full_name=settings.admin_full_name,
            is_default_admin=True,
        )
        db.add(staff)
        await db.commit()
        await db.refresh(staff)
        library_api.info("Default admin created: %s", admin_email)
        return staff
    except Exception as exc:
        library_api.error("Failed to seed default admin: %s", exc, exc_info=True)
        await db.rollback()
        return None


async def seed_sample_books(db: AsyncSession, admin_id: UUID) -> None:
    """Seed sample books for testing and demonstration when the catalog is empty.

    Only runs if no books exist in the database. Books are linked to the admin
    via ``created_by`` for a consistent audit trail from the first record.

    Args:
        db: Async database session.
        admin_id: UUID of the staff member to attribute as creator.
    """
    try:
        result = await db.execute(select(func.count()).select_from(Book))
        book_count = result.scalar_one()
        if book_count > 0:
            library_api.info("Sample books already exist, skipping")
            return

        books = [
            Book(
                title=book["title"],
                author=book["author"],
                isbn=book["isbn"],
                genre=book["genre"],
                copies_total=book["copies_total"],
                copies_available=book["copies_total"],
                created_by=admin_id,
            )
            for book in SAMPLE_BOOKS
        ]
        db.add_all(books)
        await db.commit()
        library_api.info("Seeded %s sample books", len(books))
    except Exception as exc:
        library_api.error("Failed to seed sample books: %s", exc, exc_info=True)
        await db.rollback()
