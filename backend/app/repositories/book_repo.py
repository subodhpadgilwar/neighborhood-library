"""Repository layer for book database operations. Contains only database queries — no business logic. All business rules belong in the service layer."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from app.core.logger import library_api
from app.core.timezone import now_utc
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate

_BOOK_LOAD_OPTIONS = (
    selectinload(Book.created_by_staff),
    selectinload(Book.updated_by_staff),
)


class BookRepository:
    """Data access layer for Book entities."""

    @staticmethod
    def _select_books() -> Select[tuple[Book]]:
        """Build a base SELECT for books with staff relationships eager-loaded.

        Returns:
            SQLAlchemy select statement with selectinload options applied.
        """
        return select(Book).options(*_BOOK_LOAD_OPTIONS)

    @staticmethod
    def _apply_active_filter(
        stmt: Select[tuple[Book]],
        include_inactive: bool,
    ) -> Select[tuple[Book]]:
        """Restrict a query to active books unless include_inactive is True.

        Args:
            stmt: Existing select statement to filter.
            include_inactive: When False (default), only active books are included.

        Returns:
            The statement, optionally filtered by ``Book.is_active``.
        """
        if not include_inactive:
            stmt = stmt.where(Book.is_active.is_(True))
        return stmt

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[Book]:
        """Fetch a paginated list of books.

        Args:
            db: Async database session.
            skip: Number of rows to skip for pagination.
            limit: Maximum number of rows to return.
            include_inactive: When False (default), soft-deleted books are excluded.

        Returns:
            List of Book ORM instances with staff relationships loaded.
        """
        library_api.debug(
            "BookRepository.get_all skip=%s limit=%s include_inactive=%s",
            skip,
            limit,
            include_inactive,
        )
        stmt = BookRepository._apply_active_filter(
            BookRepository._select_books(),
            include_inactive,
        )
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        book_id: UUID,
        include_inactive: bool = False,
    ) -> Book | None:
        """Fetch a single book by primary key.

        Args:
            db: Async database session.
            book_id: Book UUID.
            include_inactive: When False (default), soft-deleted books are excluded.

        Returns:
            The matching Book, or None if not found.
        """
        library_api.debug(
            "BookRepository.get_by_id book_id=%s include_inactive=%s",
            book_id,
            include_inactive,
        )
        stmt = BookRepository._apply_active_filter(
            BookRepository._select_books().where(Book.id == book_id),
            include_inactive,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_isbn(db: AsyncSession, isbn: str) -> Book | None:
        """Fetch a book by ISBN without active/inactive filtering.

        Args:
            db: Async database session.
            isbn: 13-digit ISBN string.

        Returns:
            The matching Book, or None if not found.
        """
        library_api.debug("BookRepository.get_by_isbn isbn=%s", isbn)
        result = await db.execute(
            BookRepository._select_books().where(Book.isbn == isbn)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: BookCreate) -> Book:
        """Insert a new book and reload it with relationships.

        Args:
            db: Async database session.
            data: Validated book creation payload.

        Returns:
            The persisted Book with staff relationships loaded.
        """
        library_api.debug("BookRepository.create title=%s", data.title)
        book = Book(
            **data.model_dump(),
            copies_available=data.copies_total,
        )
        db.add(book)
        await db.commit()
        loaded = await BookRepository.get_by_id(db, book.id, include_inactive=True)
        return loaded if loaded is not None else book

    @staticmethod
    async def update(db: AsyncSession, book: Book, data: BookUpdate) -> Book:
        """Apply partial field updates to an existing book.

        Args:
            db: Async database session.
            book: Existing Book ORM instance to update.
            data: Validated update payload; None fields are skipped.

        Returns:
            The updated Book with staff relationships loaded.
        """
        library_api.debug("BookRepository.update book_id=%s", book.id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(book, field, value)
        await db.commit()
        loaded = await BookRepository.get_by_id(db, book.id, include_inactive=True)
        return loaded if loaded is not None else book

    @staticmethod
    async def delete(db: AsyncSession, book: Book) -> None:
        """Permanently delete a book row.

        Args:
            db: Async database session.
            book: Book ORM instance to delete.
        """
        library_api.debug("BookRepository.delete book_id=%s", book.id)
        await db.delete(book)
        await db.commit()

    @staticmethod
    async def soft_delete(db: AsyncSession, book: Book, staff_id: UUID) -> Book:
        """Mark a book inactive and record the updating staff member.

        Args:
            db: Async database session.
            book: Book ORM instance to soft-delete.
            staff_id: UUID of the staff member performing the action.

        Returns:
            The updated Book with staff relationships loaded.
        """
        library_api.debug("BookRepository.soft_delete book_id=%s", book.id)
        book.is_active = False
        book.updated_by = staff_id
        book.updated_at = now_utc()
        await db.commit()
        loaded = await BookRepository.get_by_id(db, book.id, include_inactive=True)
        return loaded if loaded is not None else book

    @staticmethod
    async def restore(db: AsyncSession, book: Book, staff_id: UUID) -> Book:
        """Reactivate a soft-deleted book.

        Args:
            db: Async database session.
            book: Inactive Book ORM instance to restore.
            staff_id: UUID of the staff member performing the action.

        Returns:
            The updated Book with staff relationships loaded.
        """
        library_api.debug("BookRepository.restore book_id=%s", book.id)
        book.is_active = True
        book.updated_by = staff_id
        book.updated_at = now_utc()
        await db.commit()
        loaded = await BookRepository.get_by_id(db, book.id, include_inactive=True)
        return loaded if loaded is not None else book

    @staticmethod
    async def decrement_copies(db: AsyncSession, book: Book) -> Book:
        """Decrease available copy count by one after a loan is created.

        Args:
            db: Async database session.
            book: Book whose copies_available will be decremented.

        Returns:
            The updated Book with staff relationships loaded.
        """
        library_api.debug("BookRepository.decrement_copies book_id=%s", book.id)
        book.copies_available -= 1
        await db.commit()
        loaded = await BookRepository.get_by_id(db, book.id, include_inactive=True)
        return loaded if loaded is not None else book

    @staticmethod
    async def increment_copies(db: AsyncSession, book: Book) -> Book:
        """Increase available copy count by one after a return.

        Args:
            db: Async database session.
            book: Book whose copies_available will be incremented.

        Returns:
            The updated Book with staff relationships loaded.
        """
        library_api.debug("BookRepository.increment_copies book_id=%s", book.id)
        book.copies_available += 1
        await db.commit()
        loaded = await BookRepository.get_by_id(db, book.id, include_inactive=True)
        return loaded if loaded is not None else book
