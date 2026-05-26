"""Service layer for book business logic.

Orchestrates between repository layer and API layer. All business rules and
validation that requires database context live here.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookNotFoundException, DuplicateISBNException
from app.core.logger import library_api
from app.models.book import Book
from app.repositories.book_repo import BookRepository
from app.repositories.lending_repo import LendingRepository
from app.schemas.book import BookCreate, BookUpdate


class BookService:
    """Business logic for catalog book operations."""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
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
            HTTPException: If the book exists but is deactivated.
        """
        book = await BookRepository.get_by_isbn(db, isbn)
        if book is None:
            raise BookNotFoundException(isbn)

        if not book.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This book exists but is currently deactivated",
            )

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
        if data.isbn is not None:
            existing = await BookRepository.get_by_isbn(db, data.isbn)
            if existing is not None:
                raise DuplicateISBNException(data.isbn)

        book = await BookRepository.create(db, data)
        book.created_by = staff_id
        await db.commit()
        loaded = await BookRepository.get_by_id(db, book.id, include_inactive=True)
        book = loaded if loaded is not None else book
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
        """
        book = await BookRepository.get_by_id(db, book_id)
        if book is None:
            raise BookNotFoundException(book_id)

        if data.isbn is not None:
            existing = await BookRepository.get_by_isbn(db, data.isbn)
            if existing is not None and existing.id != book.id:
                raise DuplicateISBNException(data.isbn)

        book.updated_by = staff_id
        book = await BookRepository.update(db, book, data)
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
            HTTPException: If the book still has active loan(s).
        """
        book = await BookRepository.get_by_id(db, book_id, include_inactive=False)
        if book is None:
            raise BookNotFoundException(book_id)

        active_loans = await LendingRepository.get_active_by_book(db, book_id)
        if active_loans:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete book with {len(active_loans)} active loan(s)",
            )

        book = await BookRepository.soft_delete(db, book, staff_id)
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
        book = await BookRepository.get_by_id(db, book_id, include_inactive=True)
        if book is None:
            raise BookNotFoundException(book_id)

        book = await BookRepository.restore(db, book, staff_id)
        library_api.info("Book restored: %s by staff %s", book_id, staff_id)
        return book
