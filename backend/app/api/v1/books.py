"""API routes for book management.

All routes protected by JWT authentication unless noted otherwise.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_staff, get_db, get_optional_staff
from app.models.staff import Staff
from app.schemas.book import BookCreate, BookListResponse, BookResponse, BookUpdate
from app.services.book_service import BookService

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("/", response_model=BookListResponse)
async def list_books(
    db: AsyncSession = Depends(get_db),
    current_staff: Staff | None = Depends(get_optional_staff),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = Query(None, min_length=1, max_length=255),
    genre: str | None = Query(None, min_length=1, max_length=100),
    sort_by: str = Query("title", pattern="^(title|author|genre|created_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    include_inactive: bool = Query(False),
) -> BookListResponse:
    """List catalog books with server-side pagination and filtering (no JWT)."""
    if include_inactive and current_staff is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view inactive books",
        )
    return await BookService.get_page(
        db,
        page=page,
        limit=limit,
        search=search,
        genre=genre,
        sort_by=sort_by,
        sort_order=sort_order,
        include_inactive=include_inactive,
    )


@router.get("/isbn/{isbn}", response_model=BookResponse)
async def get_book_by_isbn(
    isbn: str,
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    """Look up a book by ISBN for barcode scanning (no JWT)."""
    book = await BookService.get_by_isbn(db, isbn)
    return BookResponse.model_validate(book)


@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(
    data: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> BookResponse:
    """Create a new catalog book; requires JWT."""
    book = await BookService.create(db, data, current_staff.id)
    return BookResponse.model_validate(book)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    """Get a single book by id (no JWT)."""
    book = await BookService.get_by_id(db, book_id)
    return BookResponse.model_validate(book)


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: UUID,
    data: BookUpdate,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> BookResponse:
    """Update book fields; requires JWT."""
    book = await BookService.update(db, book_id, data, current_staff.id)
    return BookResponse.model_validate(book)


@router.delete("/{book_id}", response_model=BookResponse)
async def delete_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> BookResponse:
    """Soft-delete a book when it has no active loans; requires JWT."""
    book = await BookService.soft_delete(db, book_id, current_staff.id)
    return BookResponse.model_validate(book)


@router.put("/{book_id}/restore", response_model=BookResponse)
async def restore_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff),
) -> BookResponse:
    """Restore a previously deactivated book; requires JWT."""
    book = await BookService.restore(db, book_id, current_staff.id)
    return BookResponse.model_validate(book)
