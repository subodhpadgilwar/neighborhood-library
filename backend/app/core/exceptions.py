"""Domain exceptions independent from HTTP framework concerns.

These errors are raised by services/dependencies to express business failures.
The API layer maps them to HTTP status codes and response payloads.
"""


class DomainException(Exception):
    """Base class for domain/application errors."""

    default_message = "A domain error occurred"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# 404 Not Found
# ---------------------------------------------------------------------------


class BookNotFoundException(DomainException):
    """Raised when a book ID does not exist or is not found in the database."""

    def __init__(self, book_id: int | str | None = None) -> None:
        detail = (
            f"Book not found: {book_id}" if book_id is not None else "Book not found"
        )
        super().__init__(detail)


class MemberNotFoundException(DomainException):
    """Raised when a member ID does not exist or is not found in the database."""

    def __init__(self, member_id: int | str | None = None) -> None:
        detail = (
            f"Member not found: {member_id}"
            if member_id is not None
            else "Member not found"
        )
        super().__init__(detail)


class LendingNotFoundException(DomainException):
    """Raised when a lending record ID does not exist in the database."""

    def __init__(self) -> None:
        super().__init__("Lending record not found")


class StaffNotFoundException(DomainException):
    """Raised when a staff ID does not exist or is not found in the database."""

    def __init__(self) -> None:
        super().__init__("Staff member not found")


# ---------------------------------------------------------------------------
# 400 Bad Request
# ---------------------------------------------------------------------------


class BookNotAvailableException(DomainException):
    """Raised when a borrow is attempted but no copies of the book are available."""

    def __init__(self) -> None:
        super().__init__("No copies available for this book")


class AlreadyBorrowedException(DomainException):
    """Raised when a member already has an active loan for the same book."""

    def __init__(self) -> None:
        super().__init__("Member already has this book borrowed")


class AlreadyReturnedException(DomainException):
    """Raised when a return is attempted on a loan that is already returned."""

    def __init__(self) -> None:
        super().__init__("This book has already been returned")


class BookDeactivatedException(DomainException):
    """Raised when lookup targets a soft-deleted book."""

    def __init__(self) -> None:
        super().__init__("This book exists but is currently deactivated")


class InvalidCopyCountException(DomainException):
    """Raised when total copies would fall below currently borrowed copies."""

    def __init__(self) -> None:
        super().__init__("Total copies cannot be less than currently borrowed copies")


class ActiveLoansException(DomainException):
    """Raised when deleting an entity that still has open loans."""

    def __init__(self, *, entity: str, count: int) -> None:
        super().__init__(f"Cannot delete {entity} with {count} active loan(s)")


class InvalidDueDateException(DomainException):
    """Raised when a due date is missing, in the past, or not after borrow time."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class CannotUpdateReturnedLoanException(DomainException):
    """Raised when updating due date on a closed loan."""

    def __init__(self) -> None:
        super().__init__("Cannot update due date of returned book")


class IncorrectPasswordException(DomainException):
    """Raised when the supplied current password does not match."""

    def __init__(self) -> None:
        super().__init__("Current password is incorrect")


class PasswordUnchangedException(DomainException):
    """Raised when the new password matches the current password."""

    def __init__(self) -> None:
        super().__init__("New password must differ from current")


class CannotChangeDefaultAdminRoleException(DomainException):
    """Raised when attempting to change the default admin's role."""

    def __init__(self) -> None:
        super().__init__("Cannot change the default admin role")


class CannotChangeOwnRoleException(DomainException):
    """Raised when staff attempt to change their own role."""

    def __init__(self) -> None:
        super().__init__("Cannot change your own role")


class CannotDeactivateDefaultAdminException(DomainException):
    """Raised when attempting to deactivate the default admin account."""

    def __init__(self) -> None:
        super().__init__("Cannot deactivate the default admin")


class CannotDeactivateSelfException(DomainException):
    """Raised when staff attempt to deactivate their own account."""

    def __init__(self) -> None:
        super().__init__("Cannot deactivate your own account")


# ---------------------------------------------------------------------------
# 409 Conflict
# ---------------------------------------------------------------------------


class DuplicateEmailException(DomainException):
    """Raised when creating or updating a record with an email that already exists."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Email already registered: {email}")


class DuplicateISBNException(DomainException):
    """Raised when creating or updating a book with an ISBN that already exists."""

    def __init__(self, isbn: str) -> None:
        super().__init__(f"A book with this ISBN already exists: {isbn}")


# ---------------------------------------------------------------------------
# 401 Unauthorized
# ---------------------------------------------------------------------------


class InvalidCredentialsException(DomainException):
    """Raised when login email or password does not match any staff account."""

    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class InvalidTokenException(DomainException):
    """Raised when a JWT is missing, invalid, or expired."""

    def __init__(self) -> None:
        super().__init__("Token is invalid or expired")


class AuthenticationRequiredException(DomainException):
    """Raised when an endpoint requires authentication for a requested option."""

    def __init__(self, message: str = "Authentication is required") -> None:
        super().__init__(message)


# ---------------------------------------------------------------------------
# 403 Forbidden
# ---------------------------------------------------------------------------


class AdminRequiredException(DomainException):
    """Raised when a staff account lacks permission for an admin-only action."""

    def __init__(self) -> None:
        super().__init__("Admin privileges are required for this action")
