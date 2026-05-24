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
    @staticmethod
    def _select_books() -> Select[tuple[Book]]:
        return select(Book).options(*_BOOK_LOAD_OPTIONS)

    @staticmethod
    def _apply_active_filter(
        stmt: Select[tuple[Book]],
        include_inactive: bool,
    ) -> Select[tuple[Book]]:
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
        library_api.debug("BookRepository.get_by_isbn isbn=%s", isbn)
        result = await db.execute(
            BookRepository._select_books().where(Book.isbn == isbn)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: BookCreate) -> Book:
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
        library_api.debug("BookRepository.update book_id=%s", book.id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(book, field, value)
        await db.commit()
        loaded = await BookRepository.get_by_id(db, book.id, include_inactive=True)
        return loaded if loaded is not None else book

    @staticmethod
    async def delete(db: AsyncSession, book: Book) -> None:
        library_api.debug("BookRepository.delete book_id=%s", book.id)
        await db.delete(book)
        await db.commit()

    @staticmethod
    async def soft_delete(db: AsyncSession, book: Book, staff_id: UUID) -> Book:
        library_api.debug("BookRepository.soft_delete book_id=%s", book.id)
        book.is_active = False
        book.updated_by = staff_id
        book.updated_at = now_utc()
        await db.commit()
        loaded = await BookRepository.get_by_id(db, book.id, include_inactive=True)
        return loaded if loaded is not None else book

    @staticmethod
    async def restore(db: AsyncSession, book: Book, staff_id: UUID) -> Book:
        library_api.debug("BookRepository.restore book_id=%s", book.id)
        book.is_active = True
        book.updated_by = staff_id
        book.updated_at = now_utc()
        await db.commit()
        loaded = await BookRepository.get_by_id(db, book.id, include_inactive=True)
        return loaded if loaded is not None else book

    @staticmethod
    async def decrement_copies(db: AsyncSession, book: Book) -> Book:
        library_api.debug("BookRepository.decrement_copies book_id=%s", book.id)
        book.copies_available -= 1
        await db.commit()
        loaded = await BookRepository.get_by_id(db, book.id, include_inactive=True)
        return loaded if loaded is not None else book

    @staticmethod
    async def increment_copies(db: AsyncSession, book: Book) -> Book:
        library_api.debug("BookRepository.increment_copies book_id=%s", book.id)
        book.copies_available += 1
        await db.commit()
        loaded = await BookRepository.get_by_id(db, book.id, include_inactive=True)
        return loaded if loaded is not None else book
