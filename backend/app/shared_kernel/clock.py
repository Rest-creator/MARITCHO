"""Timezone-aware time, everywhere.

`datetime.utcnow()` returns a *naive* datetime. Anything built from one and
sent straight to a client (a just-created message, a WebSocket payload)
serialises without an offset, e.g. "2026-11-17T10:00:00", which browsers
parse as *local* time: two hours early in Zimbabwe (UTC+2). Rows read back
from `timestamptz` columns are aware, so the same message showed two
different times depending on how it arrived. Use these helpers instead.
"""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """The current time as an aware UTC datetime."""
    return datetime.now(UTC)


def as_utc(value: datetime | None) -> datetime | None:
    """Treat a naive datetime as UTC (how this codebase wrote them) and
    normalise aware ones to UTC, so `.isoformat()` always carries `+00:00`."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
