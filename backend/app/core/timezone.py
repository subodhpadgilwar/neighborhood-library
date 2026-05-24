from datetime import datetime
from typing import Optional, Tuple

import pytz

from app.config import settings

UTC = pytz.UTC
MonthKey = Tuple[int, int]


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


def start_of_month_local(dt: Optional[datetime] = None) -> datetime:
    """Return the first instant of the calendar month in APP_TIMEZONE."""
    tz = get_app_timezone()
    if dt is None:
        dt = now_utc()
    local = dt.astimezone(tz)
    return local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def subtract_months(dt: datetime, months: int) -> datetime:
    """Move backward by whole calendar months, preserving timezone."""
    year = dt.year
    month = dt.month - months
    while month <= 0:
        month += 12
        year -= 1
    return dt.replace(year=year, month=month)


def month_key(dt: datetime) -> MonthKey:
    """
    Calendar (year, month) in APP_TIMEZONE.

    Naive datetimes from PostgreSQL month buckets are treated as APP_TIMEZONE
    wall time (see date_trunc on timezone-converted timestamps).
    """
    tz = get_app_timezone()
    if dt.tzinfo is None:
        local = tz.localize(dt)
    else:
        local = dt.astimezone(tz)
    return (local.year, local.month)


def format_month_label(year: int, month: int) -> str:
    """Human-readable month label, e.g. 'May 2026'."""
    label_dt = get_app_timezone().localize(datetime(year, month, 1))
    return label_dt.strftime("%b %Y")


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
