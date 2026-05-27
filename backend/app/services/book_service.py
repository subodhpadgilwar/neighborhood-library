"""Service layer for book business logic.

Orchestrates between repository layer and API layer. All business rules and
validation that requires database context live here.
"""

import math
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ActiveLoansException,
    BookDeactivatedException,
    BookNotFoundException,
    DuplicateISBNException,
    InvalidCopyCountException,
)
from app.core.logger import library_api
from app.core.unit_of_work import transaction
from app.models.book import Book
from app.repositories.book_repo import BookRepository
from app.repositories.lending_repo import LendingRepository
from app.schemas.book import BookCreate, BookListResponse, BookResponse, BookUpdate


class BookService:
    """Business logic for catalog book operations."""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: str | None = None,
        genre: str | None = None,
        sort_by: str = "title",
        sort_order: str = "asc",
    ) -> list[Book]:
        """Return a paginated list of books.

        Args:
            db: Async database session.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            include_inactive: When True, include soft-deleted books.

        Returns:
            List of Book models.
        """
        return await BookRepository.get_all(
            db,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            search=search,
            genre=genre,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    @staticmethod
    async def get_page(
        db: AsyncSession,
        page: int = 1,
        limit: int = 100,
        include_inactive: bool = False,
        search: str | None = None,
        genre: str | None = None,
        sort_by: str = "title",
        sort_order: str = "asc",
    ) -> BookListResponse:
        """Return a paginated, filterable catalog response."""
        skip = (page - 1) * limit
        books = await BookRepository.get_all(
            db,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            search=search,
            genre=genre,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        total = await BookRepository.count(
            db,
            include_inactive=include_inactive,
            search=search,
            genre=genre,
        )
        return BookListResponse(
            items=[BookResponse.model_validate(book) for book in books],
            total=total,
            page=page,
            limit=limit,
            total_pages=math.ceil(total / limit) if limit > 0 else 0,
        )

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        book_id: UUID,
        include_inactive: bool = False,
    ) -> Book:
        """Fetch a single book by primary key.

        Args:
            db: Async database session.
            book_id: Book UUID.
            include_inactive: When True, allow loading a soft-deleted book.

        Returns:
            The Book model.

        Raises:
            BookNotFoundException: If no book exists for the given id.
        """
        book = await BookRepository.get_by_id(
            db,
            book_id,
            include_inactive=include_inactive,
        )
        if book is None:
            raise BookNotFoundException(book_id)
        return book

    @staticmethod
    async def get_by_isbn(db: AsyncSession, isbn: str) -> Book:
        """Fetch an active book by ISBN for quick lookup (e.g. barcode scan).

        Args:
            db: Async database session.
            isbn: ISBN-13 string.

        Returns:
            The Book model.

        Raises:
            BookNotFoundException: If no book matches the ISBN.
            BookDeactivatedException: If the book exists but is deactivated.
        """
        book = await BookRepository.get_by_isbn(db, isbn)
        if book is None:
            raise BookNotFoundException(isbn)

        if not book.is_active:
            raise BookDeactivatedException()

        library_api.info("Book lookup by ISBN: %s", isbn)
        return book

    @staticmethod
    async def create(db: AsyncSession, data: BookCreate, staff_id: UUID) -> Book:
        """Create a new catalog book and record the creating staff member.

        Args:
            db: Async database session.
            data: Book creation payload.
            staff_id: UUID of the staff member performing the action.

        Returns:
            The persisted Book model.

        Raises:
            DuplicateISBNException: If the ISBN is already in use.
        """
        book_id: UUID
        try:
            async with transaction(db):
                if data.isbn is not None:
                    existing = await BookRepository.get_by_isbn(db, data.isbn)
                    if existing is not None:
                        raise DuplicateISBNException(data.isbn)

                book = await BookRepository.create(db, data)
                book.created_by = staff_id
                book_id = book.id
        except IntegrityError as exc:
            if data.isbn is not None:
                raise DuplicateISBNException(data.isbn) from exc
            raise

        loaded = await BookRepository.get_by_id(db, book_id, include_inactive=True)
        if loaded is None:
            raise BookNotFoundException(book_id)
        book = loaded
        library_api.info("Book created: %s", book.title)
        return book

    @staticmethod
    async def update(
        db: AsyncSession,
        book_id: UUID,
        data: BookUpdate,
        staff_id: UUID,
    ) -> Book:
        """Update an existing book's fields.

        Args:
            db: Async database session.
            book_id: Book UUID to update.
            data: Partial update payload.
            staff_id: UUID of the staff member performing the action.

        Returns:
            The updated Book model.

        Raises:
            BookNotFoundException: If the book does not exist.
            DuplicateISBNException: If the new ISBN belongs to another book.
            InvalidCopyCountException: If copies_total is below borrowed count.
        """
        updated_id: UUID
        try:
            async with transaction(db):
                book = await BookRepository.get_by_id_for_update(db, book_id)
                if book is None:
                    raise BookNotFoundException(book_id)

                if data.isbn is not None:
                    existing = await BookRepository.get_by_isbn(db, data.isbn)
                    if existing is not None and existing.id != book.id:
                        raise DuplicateISBNException(data.isbn)

                if data.copies_total is not None:
                    borrowed_count = book.copies_total - book.copies_available
                    if data.copies_total < borrowed_count:
                        raise InvalidCopyCountException()
                    book.copies_available = data.copies_total - borrowed_count

                book.updated_by = staff_id
                book = await BookRepository.update(db, book, data)
                updated_id = book.id
        except IntegrityError as exc:
            if data.isbn is not None:
                raise DuplicateISBNException(data.isbn) from exc
            raise

        loaded = await BookRepository.get_by_id(db, updated_id, include_inactive=True)
        book = loaded if loaded is not None else book
        library_api.info("Book updated: %s", book.id)
        return book

    @staticmethod
    async def soft_delete(db: AsyncSession, book_id: UUID, staff_id: UUID) -> Book:
        """Soft-delete a book when it has no active loans.

        Args:
            db: Async database session.
            book_id: Book UUID to deactivate.
            staff_id: UUID of the staff member performing the action.

        Returns:
            The deactivated Book model.

        Raises:
            BookNotFoundException: If the book does not exist or is already inactive.
            ActiveLoansException: If the book still has active loan(s).
        """
        updated_id: UUID
        async with transaction(db):
            book = await BookRepository.get_by_id_for_update(
                db,
                book_id,
                include_inactive=False,
            )
            if book is None:
                raise BookNotFoundException(book_id)

            active_loans = await LendingRepository.get_active_by_book(db, book_id)
            if active_loans:
                raise ActiveLoansException(entity="book", count=len(active_loans))

            book = await BookRepository.soft_delete(db, book, staff_id)
            updated_id = book.id

        loaded = await BookRepository.get_by_id(db, updated_id, include_inactive=True)
        book = loaded if loaded is not None else book
        library_api.info("Book soft deleted: %s by staff %s", book_id, staff_id)
        return book

    @staticmethod
    async def restore(db: AsyncSession, book_id: UUID, staff_id: UUID) -> Book:
        """Reactivate a previously soft-deleted book.

        Args:
            db: Async database session.
            book_id: Book UUID to restore.
            staff_id: UUID of the staff member performing the action.

        Returns:
            The restored Book model.

        Raises:
            BookNotFoundException: If no book exists for the given id.
        """
        updated_id: UUID
        async with transaction(db):
            book = await BookRepository.get_by_id_for_update(
                db,
                book_id,
                include_inactive=True,
            )
            if book is None:
                raise BookNotFoundException(book_id)

            book = await BookRepository.restore(db, book, staff_id)
            updated_id = book.id

        loaded = await BookRepository.get_by_id(db, updated_id, include_inactive=True)
        book = loaded if loaded is not None else book
        library_api.info("Book restored: %s by staff %s", book_id, staff_id)
        return book
