import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import pytz

from app.config import BASE_DIR, settings

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"
LOGGER_NAME = "library_api"


class LocalTimezoneFormatter(logging.Formatter):
    """Format log timestamps in the configured application timezone."""

    def __init__(self, timezone_name: str) -> None:
        super().__init__(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
        self._tz = pytz.timezone(timezone_name)

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=self._tz)
        tz_label = dt.tzname() or settings.app_timezone
        return dt.strftime("%Y-%m-%d %H:%M:%S") + f" {tz_label}"


def _resolve_log_level(level_name: str) -> int:
    level = getattr(logging, level_name.upper(), None)
    if isinstance(level, int):
        return level
    return logging.INFO


def _configure_logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = LocalTimezoneFormatter(settings.app_timezone)

    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=settings.log_retention_days,
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(_resolve_log_level(settings.log_level))
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger


library_api = _configure_logger()
