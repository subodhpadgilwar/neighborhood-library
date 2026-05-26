"""Logging configuration for the library API.

Sets up a timezone-aware rotating file handler and console handler with
timestamps displayed in ``APP_TIMEZONE``.
"""

import logging
import os
import time
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import pytz

from app.config import BASE_DIR, settings

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"
LOGGER_NAME = "library_api"


class LocalTimezoneFormatter(logging.Formatter):
    """Custom log formatter that displays timestamps in the configured app timezone.

    Instead of UTC or server local time, log lines show wall-clock time in
    ``APP_TIMEZONE`` with a timezone abbreviation suffix.
    """

    def __init__(self, timezone_name: str) -> None:
        """Initialize formatter with the given IANA timezone name.

        Args:
            timezone_name: IANA timezone string (e.g. ``Asia/Kolkata``).
        """
        super().__init__(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
        self._tz = pytz.timezone(timezone_name)

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        """Convert UTC log timestamp to local timezone for display.

        Args:
            record: Log record whose ``created`` epoch time is formatted.
            datefmt: Optional strftime format (unused; fixed format is used).

        Returns:
            Formatted timestamp string with timezone label.
        """
        dt = datetime.fromtimestamp(record.created, tz=self._tz)
        tz_label = dt.tzname() or settings.app_timezone
        return dt.strftime("%Y-%m-%d %H:%M:%S") + f" {tz_label}"


class AppTimezoneTimedRotatingFileHandler(TimedRotatingFileHandler):
    """Rotate log files at midnight in APP_TIMEZONE (not system local time).

    TimedRotatingFileHandler defaults to the server's local timezone, which
    breaks rotation when APP_TIMEZONE differs (e.g. Asia/Kolkata on a US host).

    Attributes:
        _app_tz: pytz timezone used for rollover calculations.
    """

    def __init__(
        self,
        filename: str | os.PathLike[str],
        *,
        timezone_name: str,
        backup_count: int,
        encoding: str = "utf-8",
    ) -> None:
        """Create a file handler that rotates at app-timezone midnight.

        Args:
            filename: Path to the active log file.
            timezone_name: IANA timezone for midnight rollover.
            backup_count: Number of rotated backup files to retain.
            encoding: File encoding (default UTF-8).
        """
        self._app_tz = pytz.timezone(timezone_name)
        super().__init__(
            filename=filename,
            when="midnight",
            interval=1,
            backupCount=backup_count,
            encoding=encoding,
            utc=False,
        )
        self.suffix = "%Y-%m-%d"
        self.rolloverAt = self.computeRollover(time.time())

    def computeRollover(self, currentTime: float) -> float:
        """Compute next rollover timestamp at midnight in APP_TIMEZONE.

        Args:
            currentTime: Current time as Unix epoch seconds.

        Returns:
            Epoch seconds of the next scheduled rollover.
        """
        current = datetime.fromtimestamp(currentTime, self._app_tz)
        rollover = current.replace(hour=0, minute=0, second=0, microsecond=0)
        if currentTime >= rollover.timestamp():
            rollover += timedelta(days=1)
        return rollover.timestamp()

    def doRollover(self) -> None:
        """Close the stream before renaming to avoid file locks on Windows."""
        if self.stream:
            self.stream.close()
            self.stream = None
        super().doRollover()


def _resolve_log_level(level_name: str) -> int:
    """Map a log level name string to a logging module constant.

    Args:
        level_name: Level name such as ``INFO`` or ``DEBUG``.

    Returns:
        Numeric log level; defaults to ``logging.INFO`` if unknown.
    """
    level = getattr(logging, level_name.upper(), None)
    if isinstance(level, int):
        return level
    return logging.INFO


def _configure_logger() -> logging.Logger:
    """Configure and return the application logger with file rotation and console output.

    Idempotent: skips re-configuration if the logger was already set up in this
    process. File handler rotates daily at APP_TIMEZONE midnight; console
    handler mirrors output at DEBUG level.

    Returns:
        Configured ``library_api`` logger instance.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    if getattr(logger, "_library_api_configured", False):
        return logger

    formatter = LocalTimezoneFormatter(settings.app_timezone)

    file_handler = AppTimezoneTimedRotatingFileHandler(
        LOG_FILE,
        timezone_name=settings.app_timezone,
        backup_count=settings.log_retention_days,
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    logger.setLevel(_resolve_log_level(settings.log_level))
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    logger._library_api_configured = True  # type: ignore[attr-defined]

    return logger


library_api = _configure_logger()
