"""Timezone utilities for the library API.

All datetimes are stored as UTC in the database and converted to the configured
local timezone (``APP_TIMEZONE``) for API responses and analytics bucketing.
"""

from datetime import datetime
from typing import Optional, Tuple

import pytz

from app.config import settings

UTC = pytz.UTC
MonthKey = Tuple[int, int]


def get_app_timezone() -> pytz.BaseTzInfo:
    """Return the configured pytz timezone object from ``APP_TIMEZONE``.

    Returns:
        pytz timezone instance for the application locale.
    """
    return pytz.timezone(settings.app_timezone)


def now_utc() -> datetime:
    """Return the current UTC datetime, timezone-aware.

    Use this everywhere instead of ``datetime.utcnow()``, which returns a naive
    datetime and can cause comparison bugs with timezone-aware columns.

    Returns:
        Current time as an aware UTC ``datetime``.
    """
    return datetime.now(UTC)


def to_local(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert a UTC datetime to the configured local timezone.

    Naive datetimes are treated as UTC. Returns None when ``dt`` is None.

    Args:
        dt: UTC or naive datetime to convert, or None.

    Returns:
        Timezone-aware datetime in ``APP_TIMEZONE``, or None.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = UTC.localize(dt)
    else:
        dt = dt.astimezone(UTC)

    return dt.astimezone(get_app_timezone())


def start_of_month_local(dt: Optional[datetime] = None) -> datetime:
    """Return the first instant of the calendar month in APP_TIMEZONE.

    Args:
        dt: Reference instant (UTC-aware); defaults to ``now_utc()`` when None.

    Returns:
        Timezone-aware datetime at 00:00:00 on the first day of that month.
    """
    tz = get_app_timezone()
    if dt is None:
        dt = now_utc()
    local = dt.astimezone(tz)
    return local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def subtract_months(dt: datetime, months: int) -> datetime:
    """Move backward by whole calendar months, preserving timezone.

    Args:
        dt: Starting datetime (typically timezone-aware).
        months: Number of whole months to subtract (non-negative).

    Returns:
        Datetime in the same timezone, earlier by ``months`` calendar months.
    """
    year = dt.year
    month = dt.month - months
    while month <= 0:
        month += 12
        year -= 1
    return dt.replace(year=year, month=month)


def month_key(dt: datetime) -> MonthKey:
    """Return calendar (year, month) in APP_TIMEZONE for analytics grouping.

    Naive datetimes from PostgreSQL month buckets are treated as APP_TIMEZONE
    wall time (see ``date_trunc`` on timezone-converted timestamps).

    Args:
        dt: Datetime from a query bucket or synthetic month start.

    Returns:
        Tuple ``(year, month)`` for use as a dict key.
    """
    tz = get_app_timezone()
    if dt.tzinfo is None:
        local = tz.localize(dt)
    else:
        local = dt.astimezone(tz)
    return (local.year, local.month)


def format_month_label(year: int, month: int) -> str:
    """Format a calendar month as a human-readable label (e.g. ``May 2026``).

    Args:
        year: Four-digit year.
        month: Month number 1–12.

    Returns:
        Abbreviated month and year string in ``APP_TIMEZONE``.
    """
    label_dt = get_app_timezone().localize(datetime(year, month, 1))
    return label_dt.strftime("%b %Y")


def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert a local datetime to UTC.

    Used when receiving datetime input from the frontend. Naive datetimes are
    assumed to be in ``APP_TIMEZONE``.

    Args:
        dt: Local or naive datetime to convert, or None.

    Returns:
        Timezone-aware UTC ``datetime``, or None.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = get_app_timezone().localize(dt)

    return dt.astimezone(UTC)
