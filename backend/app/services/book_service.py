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
    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[Book]:
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
        book = await BookRepository.get_by_id(db, book_id, include_inactive=True)
        if book is None:
            raise BookNotFoundException(book_id)

        book = await BookRepository.restore(db, book, staff_id)
        library_api.info("Book restored: %s by staff %s", book_id, staff_id)
        return book
