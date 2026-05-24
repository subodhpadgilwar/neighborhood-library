from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BookNotFoundException, DuplicateISBNException
from app.core.logger import library_api
from app.models.book import Book
from app.repositories.book_repo import BookRepository
from app.schemas.book import BookCreate, BookUpdate


class BookService:
    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Book]:
        return await BookRepository.get_all(db, skip=skip, limit=limit)

    @staticmethod
    async def get_by_id(db: AsyncSession, book_id: UUID) -> Book:
        book = await BookRepository.get_by_id(db, book_id)
        if book is None:
            raise BookNotFoundException(book_id)
        return book

    @staticmethod
    async def create(db: AsyncSession, data: BookCreate, staff_id: UUID) -> Book:
        if data.isbn is not None:
            existing = await BookRepository.get_by_isbn(db, data.isbn)
            if existing is not None:
                raise DuplicateISBNException(data.isbn)

        book = await BookRepository.create(db, data)
        book.created_by = staff_id
        await db.commit()
        await db.refresh(book)
        library_api.info("Book created: %s", book.title)
        return book

    @staticmethod
    async def update(
        db: AsyncSession,
        book_id: UUID,
        data: BookUpdate,
        staff_id: UUID,
    ) -> Book:
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
    async def delete(db: AsyncSession, book_id: UUID, staff_id: UUID) -> None:
        book = await BookRepository.get_by_id(db, book_id)
        if book is None:
            raise BookNotFoundException(book_id)

        await BookRepository.delete(db, book)
        library_api.info("Book deleted: %s by staff %s", book_id, staff_id)
