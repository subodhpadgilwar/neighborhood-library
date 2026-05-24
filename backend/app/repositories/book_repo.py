from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import library_api
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate


class BookRepository:
    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Book]:
        library_api.debug("BookRepository.get_all skip=%s limit=%s", skip, limit)
        result = await db.execute(select(Book).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, book_id: UUID) -> Book | None:
        library_api.debug("BookRepository.get_by_id book_id=%s", book_id)
        result = await db.execute(select(Book).where(Book.id == book_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_isbn(db: AsyncSession, isbn: str) -> Book | None:
        library_api.debug("BookRepository.get_by_isbn isbn=%s", isbn)
        result = await db.execute(select(Book).where(Book.isbn == isbn))
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
        await db.refresh(book)
        return book

    @staticmethod
    async def update(db: AsyncSession, book: Book, data: BookUpdate) -> Book:
        library_api.debug("BookRepository.update book_id=%s", book.id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(book, field, value)
        await db.commit()
        await db.refresh(book)
        return book

    @staticmethod
    async def delete(db: AsyncSession, book: Book) -> None:
        library_api.debug("BookRepository.delete book_id=%s", book.id)
        await db.delete(book)
        await db.commit()

    @staticmethod
    async def decrement_copies(db: AsyncSession, book: Book) -> Book:
        library_api.debug("BookRepository.decrement_copies book_id=%s", book.id)
        book.copies_available -= 1
        await db.commit()
        await db.refresh(book)
        return book

    @staticmethod
    async def increment_copies(db: AsyncSession, book: Book) -> Book:
        library_api.debug("BookRepository.increment_copies book_id=%s", book.id)
        book.copies_available += 1
        await db.commit()
        await db.refresh(book)
        return book
