"""Fixtures for PostgreSQL-backed integration tests."""

from __future__ import annotations

import os
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.main import app

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:your_postgres_password@localhost:5433/"
    "neighborhood_library_test"
)


def _test_database_url() -> str:
    return os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)


async def _ensure_test_database_exists(url: str) -> None:
    """Create the integration test database when Postgres is up but DB is missing."""
    url_obj = make_url(url)
    database_name = url_obj.database
    if not database_name:
        return

    admin_url = url_obj.set(database="postgres")
    engine = create_async_engine(admin_url, pool_pre_ping=True, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            exists = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": database_name},
            )
            if exists.scalar() is None:
                await conn.execute(text(f'CREATE DATABASE "{database_name}"'))
    finally:
        await engine.dispose()


async def _database_reachable(url: str) -> bool:
    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        await engine.dispose()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: tests that require a running PostgreSQL database",
    )


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Resolved integration test database URL."""
    return _test_database_url()


@pytest.fixture(scope="session")
def migrated_database(test_database_url: str) -> str:
    """Apply Alembic migrations once per test session."""
    if os.environ.get("SKIP_INTEGRATION_TESTS", "").lower() in {"1", "true", "yes"}:
        pytest.skip("SKIP_INTEGRATION_TESTS is set")

    import asyncio

    admin_probe_url = make_url(test_database_url).set(database="postgres")
    if not asyncio.run(_database_reachable(str(admin_probe_url))):
        pytest.skip(
            "PostgreSQL is not reachable for integration tests. "
            f"Set TEST_DATABASE_URL (current: {test_database_url}) "
            "or start docker-compose postgres on port 5433.",
        )

    asyncio.run(_ensure_test_database_exists(test_database_url))

    if not asyncio.run(_database_reachable(test_database_url)):
        pytest.skip(f"Could not connect to test database: {test_database_url}")

    env = {**os.environ, "DATABASE_URL": test_database_url}
    subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=env,
        check=True,
        capture_output=True,
    )
    return test_database_url


@pytest_asyncio.fixture
async def db_session(migrated_database: str) -> AsyncGenerator[AsyncSession, None]:
    """Yield a clean database session; truncate all tables after each test."""
    engine = create_async_engine(migrated_database, pool_pre_ping=True)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    table_names = ", ".join(
        f'"{table.name}"' for table in reversed(Base.metadata.sorted_tables)
    )
    if table_names:
        async with engine.begin() as conn:
            await conn.execute(
                text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"),
            )
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client wired to the real app with a per-test database session."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()
