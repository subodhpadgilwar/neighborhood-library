"""Entry point for the Neighborhood Library API.

Configures the FastAPI application, middleware, exception handlers, and
startup/shutdown lifecycle hooks that seed the database on boot.
"""

import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.api.v1.router import api_router
from app.config import settings
from app.core.logger import library_api
from app.core.seeder import seed_default_admin, seed_sample_books
from app.database import AsyncSessionLocal

API_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown.

    On startup, runs database seeders (default admin and sample books).
    On shutdown, logs a clean exit message.

    Args:
        app: FastAPI application instance.

    Yields:
        Control to the running application between startup and shutdown.
    """
    library_api.info("Starting Neighborhood Library API")
    library_api.info("Environment: %s", settings.app_env)
    library_api.info("Timezone: %s", settings.app_timezone)

    async with AsyncSessionLocal() as db:
        admin = await seed_default_admin(db)
        if admin is not None:
            await seed_sample_books(db, admin.id)

    library_api.info("API is ready")
    yield
    library_api.info("Shutting down API")


app = FastAPI(
    title="Neighborhood Library API",
    version=API_VERSION,
    description="REST API for managing a neighborhood library",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each HTTP request method, path, status code, and duration."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process a request and log timing metadata.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler in the chain.

        Returns:
            HTTP response from downstream handlers.
        """
        start = time.perf_counter()
        library_api.info("%s %s", request.method, request.url.path)

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        library_api.info(
            "%s %s %s %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


app.add_middleware(RequestLoggingMiddleware)


def _format_validation_errors(exc: RequestValidationError) -> list[dict[str, str]]:
    """Convert Pydantic validation errors into a flat field/message list.

    Args:
        exc: FastAPI request validation exception.

    Returns:
        List of dicts with ``field`` and ``message`` keys for JSON responses.
    """
    errors: list[dict[str, str]] = []
    for error in exc.errors():
        location = error.get("loc", ())
        field_parts = [str(part) for part in location]
        if field_parts and field_parts[0] == "body":
            field_parts = field_parts[1:]
        field = ".".join(field_parts) if field_parts else "body"
        errors.append(
            {
                "field": field,
                "message": error.get("msg", "Invalid value"),
            }
        )
    return errors


def _http_exception_message(detail: Any) -> str:
    """Extract a string message from HTTPException detail payloads.

    Args:
        detail: ``HTTPException.detail`` value (str, dict, or other).

    Returns:
        Human-readable error message string.
    """
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        message = detail.get("message")
        if isinstance(message, str):
            return message
    return str(detail)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Convert Pydantic validation errors to a consistent JSON response format.

    Args:
        request: HTTP request that failed validation.
        exc: Validation exception with field-level error details.

    Returns:
        JSONResponse with status 422 and structured ``errors`` list.
    """
    library_api.warning(
        "Validation failed for %s %s: %s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Validation failed",
            "errors": _format_validation_errors(exc),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Convert HTTPExceptions to a consistent JSON response format.

    Args:
        request: HTTP request that raised the exception.
        exc: FastAPI HTTP exception with status code and detail.

    Returns:
        JSONResponse matching the API error envelope (``status``, ``message``).
    """
    library_api.warning(
        "HTTP %s for %s %s: %s",
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": _http_exception_message(exc.detail),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """Handle SQLAlchemy errors without exposing raw database details to clients.

    Args:
        request: HTTP request during which the database error occurred.
        exc: SQLAlchemy exception (logged with full traceback server-side).

    Returns:
        JSONResponse with status 500 and a generic database error message.
    """
    library_api.error(
        "Database error on %s %s",
        request.method,
        request.url.path,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "A database error occurred",
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch all unhandled exceptions and return a safe 500 response.

    Args:
        request: HTTP request during which the unexpected error occurred.
        exc: Unhandled exception (logged with full traceback server-side).

    Returns:
        JSONResponse with status 500 and a generic error message.
    """
    library_api.error(
        "Unexpected error on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected error occurred",
        },
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return API health status and version for load balancers and monitoring.

    Returns:
        Dict with ``status`` (``ok``) and ``version`` strings.
    """
    return {"status": "ok", "version": API_VERSION}


app.include_router(api_router, prefix="/api/v1")
