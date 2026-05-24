from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_staff, get_db
from app.models.staff import Staff
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.services.book_service import BookService

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("/", response_model=list[BookResponse])
async def list_books(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_inactive: bool = False,
) -> list[BookResponse]:
    books = await BookService.get_all(
        db,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
    )
    return [BookResponse.model_validate(book) for book in books]


@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(
    data: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> BookResponse:
    book = await BookService.create(db, data, current_staff.id)
    return BookResponse.model_validate(book)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    book = await BookService.get_by_id(db, book_id)
    return BookResponse.model_validate(book)


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: UUID,
    data: BookUpdate,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> BookResponse:
    book = await BookService.update(db, book_id, data, current_staff.id)
    return BookResponse.model_validate(book)


@router.delete("/{book_id}", response_model=BookResponse)
async def delete_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> BookResponse:
    book = await BookService.soft_delete(db, book_id, current_staff.id)
    return BookResponse.model_validate(book)


@router.put("/{book_id}/restore", response_model=BookResponse)
async def restore_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> BookResponse:
    book = await BookService.restore(db, book_id, current_staff.id)
    return BookResponse.model_validate(book)
