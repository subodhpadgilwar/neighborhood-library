"""Custom HTTP exceptions for the library API.

Using custom exception classes instead of raw HTTPException provides:

- Consistent error messages across the codebase
- A single place to update error messages
- Self-documenting code (``BookNotFoundException`` is clearer than HTTPException(404))
- Easier testing and mocking in services
"""

from fastapi import HTTPException, status

_BEARER_AUTH_HEADERS = {"WWW-Authenticate": "Bearer"}


# ---------------------------------------------------------------------------
# 404 Not Found
# ---------------------------------------------------------------------------


class BookNotFoundException(HTTPException):
    """Raised when a book ID does not exist or is not found in the database."""

    def __init__(self, book_id: int | str | None = None) -> None:
        detail = (
            f"Book not found: {book_id}" if book_id is not None else "Book not found"
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class MemberNotFoundException(HTTPException):
    """Raised when a member ID does not exist or is not found in the database."""

    def __init__(self, member_id: int | str | None = None) -> None:
        detail = (
            f"Member not found: {member_id}"
            if member_id is not None
            else "Member not found"
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class LendingNotFoundException(HTTPException):
    """Raised when a lending record ID does not exist in the database."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lending record not found",
        )


class StaffNotFoundException(HTTPException):
    """Raised when a staff ID does not exist or is not found in the database."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found",
        )


# ---------------------------------------------------------------------------
# 400 Bad Request
# ---------------------------------------------------------------------------


class BookNotAvailableException(HTTPException):
    """Raised when a borrow is attempted but no copies of the book are available."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No copies available for this book",
        )


class AlreadyBorrowedException(HTTPException):
    """Raised when a member already has an active loan for the same book."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Member already has this book borrowed",
        )


class AlreadyReturnedException(HTTPException):
    """Raised when a return is attempted on a loan that is already returned."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This book has already been returned",
        )


# ---------------------------------------------------------------------------
# 409 Conflict
# ---------------------------------------------------------------------------


class DuplicateEmailException(HTTPException):
    """Raised when creating or updating a record with an email that already exists."""

    def __init__(self, email: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email already registered: {email}",
        )


class DuplicateISBNException(HTTPException):
    """Raised when creating or updating a book with an ISBN that already exists."""

    def __init__(self, isbn: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A book with this ISBN already exists: {isbn}",
        )


# ---------------------------------------------------------------------------
# 401 Unauthorized
# ---------------------------------------------------------------------------


class InvalidCredentialsException(HTTPException):
    """Raised when login email or password does not match any staff account."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers=_BEARER_AUTH_HEADERS,
        )


class InvalidTokenException(HTTPException):
    """Raised when a JWT is missing, invalid, or expired."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers=_BEARER_AUTH_HEADERS,
        )


# ---------------------------------------------------------------------------
# 403 Forbidden
# ---------------------------------------------------------------------------


class AdminRequiredException(HTTPException):
    """Raised when a staff account lacks permission for an admin-only action."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges are required for this action",
        )
