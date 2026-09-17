"""
GrowX Platform Standard Time Primitives.
Ensures timezone-aware UTC timestamps and standard ISO 8601 formatting.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional


def utc_now() -> datetime:
    """Returns the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def utc_iso_now() -> str:
    """Returns the current ISO 8601 UTC timestamp string formatted with 'Z'."""
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def calculate_future_utc_iso(hours: int = 0, days: int = 0, seconds: int = 0) -> str:
    """Calculates future ISO 8601 timestamp string based on delta."""
    future = utc_now() + timedelta(hours=hours, days=days, seconds=seconds)
    return future.strftime("%Y-%m-%dT%H:%M:%SZ")


def format_iso(dt: Optional[datetime]) -> Optional[str]:
    """Formats a datetime to ISO 8601 string or returns None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(iso_str: Optional[str]) -> Optional[datetime]:
    """Parses an ISO 8601 timestamp string into timezone-aware UTC datetime."""
    if not iso_str:
        return None
    cleaned = iso_str.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None
