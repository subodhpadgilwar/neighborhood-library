"""Application configuration using Pydantic BaseSettings.

All settings are read from environment variables or the ``.env`` file in the
backend project root. Used across database, auth, logging, and seeding.
"""

from pathlib import Path

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Field groups:
        Database: PostgreSQL connection (user, password, host, port, URL).
        App: Runtime environment name and HTTP port.
        Auth: JWT secret, algorithm, and token expiry.
        Admin: Default admin account created on first startup.
        Timezone: Application timezone for API responses and logging.
        Logging: Log level and rotated file retention count.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_db: str = "neighborhood_library"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str = (
        "postgresql+asyncpg://postgres@localhost:5432/neighborhood_library"
    )

    # App
    app_env: str = "development"
    app_port: int = 8000

    # Auth
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # Default Admin
    admin_email: EmailStr = "admin@example.com"
    admin_password: str = "change-me"
    admin_full_name: str = "Admin User"

    # Timezone
    app_timezone: str = "Asia/Kolkata"

    # Logging
    log_level: str = "INFO"
    log_retention_days: int = Field(default=30, ge=1)

    @property
    def is_development(self) -> bool:
        """Return True when ``app_env`` is ``development`` (case-insensitive)."""
        return self.app_env.lower() == "development"


settings = Settings()
