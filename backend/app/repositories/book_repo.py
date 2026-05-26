"""Repository layer for book database operations. Contains only database queries — no business logic. All business rules belong in the service layer."""

from uuid import UUID

from sqlalchemy import func, or_, select
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
    def _apply_search_filter(
        stmt: Select[tuple[Book]],
        search: str | None,
        genre: str | None,
    ) -> Select[tuple[Book]]:
        """Apply optional catalog search filters to a book query."""
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Book.title.ilike(pattern),
                    Book.author.ilike(pattern),
                    Book.isbn.ilike(pattern),
                    Book.shelf_location.ilike(pattern),
                )
            )
        if genre:
            stmt = stmt.where(Book.genre.ilike(genre.strip()))
        return stmt

    @staticmethod
    def _apply_sort(
        stmt: Select[tuple[Book]],
        sort_by: str,
        sort_order: str,
    ) -> Select[tuple[Book]]:
        """Apply a safe sort expression for catalog lists."""
        columns = {
            "title": Book.title,
            "author": Book.author,
            "genre": Book.genre,
            "created_at": Book.created_at,
        }
        sort_column = columns.get(sort_by, Book.title)
        if sort_order == "desc":
            return stmt.order_by(sort_column.desc())
        return stmt.order_by(sort_column.asc())

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
        stmt = BookRepository._apply_search_filter(stmt, search, genre)
        stmt = BookRepository._apply_sort(stmt, sort_by, sort_order)
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def count(
        db: AsyncSession,
        include_inactive: bool = False,
        search: str | None = None,
        genre: str | None = None,
    ) -> int:
        """Count books matching the same filters used by ``get_all``."""
        stmt = BookRepository._apply_active_filter(select(Book), include_inactive)
        stmt = BookRepository._apply_search_filter(stmt, search, genre).subquery()
        result = await db.execute(select(func.count()).select_from(stmt))
        return int(result.scalar_one())

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
    async def get_by_id_for_update(
        db: AsyncSession,
        book_id: UUID,
        include_inactive: bool = False,
    ) -> Book | None:
        """Fetch a book row with a write lock for inventory-sensitive updates."""
        library_api.debug(
            "BookRepository.get_by_id_for_update book_id=%s include_inactive=%s",
            book_id,
            include_inactive,
        )
        stmt = BookRepository._apply_active_filter(
            BookRepository._select_books().where(Book.id == book_id),
            include_inactive,
        ).with_for_update()
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
        await db.flush()
        return book

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
        await db.flush()
        return book

    @staticmethod
    async def delete(db: AsyncSession, book: Book) -> None:
        """Permanently delete a book row.

        Args:
            db: Async database session.
            book: Book ORM instance to delete.
        """
        library_api.debug("BookRepository.delete book_id=%s", book.id)
        await db.delete(book)
        await db.flush()

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
        await db.flush()
        return book

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
        await db.flush()
        return book

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
        await db.flush()
        return book

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
        await db.flush()
        return book
