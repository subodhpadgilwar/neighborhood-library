"""Map framework-agnostic domain exceptions to HTTP response details."""

from fastapi import status

from app.core.exceptions import (
    ActiveLoansException,
    AdminRequiredException,
    AuthenticationRequiredException,
    AlreadyBorrowedException,
    AlreadyReturnedException,
    BookDeactivatedException,
    BookNotAvailableException,
    BookNotFoundException,
    CannotChangeDefaultAdminRoleException,
    CannotChangeOwnRoleException,
    CannotDeactivateDefaultAdminException,
    CannotDeactivateSelfException,
    CannotUpdateReturnedLoanException,
    DomainException,
    DuplicateEmailException,
    DuplicateISBNException,
    IncorrectPasswordException,
    InvalidCopyCountException,
    InvalidCredentialsException,
    InvalidDueDateException,
    InvalidTokenException,
    LendingNotFoundException,
    MemberNotFoundException,
    PasswordUnchangedException,
    StaffNotFoundException,
)

_BEARER_AUTH_HEADERS = {"WWW-Authenticate": "Bearer"}


def map_domain_exception(exc: DomainException) -> tuple[int, str, dict[str, str] | None]:
    """Return HTTP status, message, and optional headers for a domain exception."""
    if isinstance(
        exc,
        (
            BookNotFoundException,
            MemberNotFoundException,
            LendingNotFoundException,
            StaffNotFoundException,
        ),
    ):
        return status.HTTP_404_NOT_FOUND, exc.message, None

    if isinstance(exc, (DuplicateEmailException, DuplicateISBNException)):
        return status.HTTP_409_CONFLICT, exc.message, None

    if isinstance(
        exc,
        (
            InvalidCredentialsException,
            InvalidTokenException,
            AuthenticationRequiredException,
        ),
    ):
        return status.HTTP_401_UNAUTHORIZED, exc.message, _BEARER_AUTH_HEADERS

    if isinstance(exc, AdminRequiredException):
        return status.HTTP_403_FORBIDDEN, exc.message, None

    if isinstance(
        exc,
        (
            BookNotAvailableException,
            AlreadyBorrowedException,
            AlreadyReturnedException,
            BookDeactivatedException,
            InvalidCopyCountException,
            ActiveLoansException,
            InvalidDueDateException,
            CannotUpdateReturnedLoanException,
            IncorrectPasswordException,
            PasswordUnchangedException,
            CannotChangeDefaultAdminRoleException,
            CannotChangeOwnRoleException,
            CannotDeactivateDefaultAdminException,
            CannotDeactivateSelfException,
        ),
    ):
        return status.HTTP_400_BAD_REQUEST, exc.message, None

    return status.HTTP_500_INTERNAL_SERVER_ERROR, exc.message, None
