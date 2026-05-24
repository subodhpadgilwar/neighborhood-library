"""
Custom HTTP exceptions for the Neighborhood Library API.

Use these classes in services and repositories instead of raising raw
HTTPException directly. They encode consistent status codes, messages,
and headers so API behavior stays uniform and routes stay thin.
"""

from fastapi import HTTPException, status

_BEARER_AUTH_HEADERS = {"WWW-Authenticate": "Bearer"}


# ---------------------------------------------------------------------------
# 404 Not Found
# ---------------------------------------------------------------------------


class BookNotFoundException(HTTPException):
    def __init__(self, book_id: int | str | None = None) -> None:
        detail = (
            f"Book not found: {book_id}" if book_id is not None else "Book not found"
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class MemberNotFoundException(HTTPException):
    def __init__(self, member_id: int | str | None = None) -> None:
        detail = (
            f"Member not found: {member_id}"
            if member_id is not None
            else "Member not found"
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class LendingNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lending record not found",
        )


class StaffNotFoundException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found",
        )


# ---------------------------------------------------------------------------
# 400 Bad Request
# ---------------------------------------------------------------------------


class BookNotAvailableException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No copies available for this book",
        )


class AlreadyBorrowedException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Member already has this book borrowed",
        )


class AlreadyReturnedException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This book has already been returned",
        )


# ---------------------------------------------------------------------------
# 409 Conflict
# ---------------------------------------------------------------------------


class DuplicateEmailException(HTTPException):
    def __init__(self, email: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email already registered: {email}",
        )


class DuplicateISBNException(HTTPException):
    def __init__(self, isbn: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A book with this ISBN already exists: {isbn}",
        )


# ---------------------------------------------------------------------------
# 401 Unauthorized
# ---------------------------------------------------------------------------


class InvalidCredentialsException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers=_BEARER_AUTH_HEADERS,
        )


class InvalidTokenException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers=_BEARER_AUTH_HEADERS,
        )
