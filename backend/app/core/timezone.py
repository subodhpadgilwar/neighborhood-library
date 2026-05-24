from datetime import datetime
from typing import Optional

import pytz

from app.config import settings

UTC = pytz.UTC


def get_app_timezone() -> pytz.BaseTzInfo:
    """Return the configured application timezone as a pytz timezone object."""
    return pytz.timezone(settings.app_timezone)


def now_utc() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def to_local(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert a UTC datetime to the application local timezone.

    Naive datetimes are treated as UTC. Returns a timezone-aware datetime
    in APP_TIMEZONE, or None if dt is None.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = UTC.localize(dt)
    else:
        dt = dt.astimezone(UTC)

    return dt.astimezone(get_app_timezone())


def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert a datetime to UTC.

    Naive datetimes are assumed to be in APP_TIMEZONE. Returns a
    timezone-aware UTC datetime, or None if dt is None.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = get_app_timezone().localize(dt)

    return dt.astimezone(UTC)
