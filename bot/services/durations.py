from __future__ import annotations

import re
from datetime import timedelta

MAX_TIMEOUT = timedelta(days=28)

_UNIT_SECONDS = {
    "s": 1,
    "sec": 1,
    "secs": 1,
    "second": 1,
    "seconds": 1,
    "m": 60,
    "min": 60,
    "mins": 60,
    "minute": 60,
    "minutes": 60,
    "h": 3600,
    "hr": 3600,
    "hrs": 3600,
    "hour": 3600,
    "hours": 3600,
    "d": 86400,
    "day": 86400,
    "days": 86400,
    "w": 604800,
    "week": 604800,
    "weeks": 604800,
}

_TOKEN_RE = re.compile(
    r"(\d+)\s*(weeks?|w|days?|d|hours?|hrs?|hr|h|minutes?|mins?|min|m|seconds?|secs?|sec|s)",
    re.IGNORECASE,
)


def parse_duration(text: str | None) -> timedelta | None:
    """Parse strings like '10m', '1h30m', '2 days' into a timedelta.

    A bare number is treated as minutes. Returns None when invalid or zero.
    Result is capped at Discord's 28-day timeout maximum.
    """
    if not text or not text.strip():
        return None
    raw = text.strip().lower().replace(",", " ")
    if raw.isdigit():
        seconds = int(raw) * 60
        return timedelta(seconds=min(seconds, int(MAX_TIMEOUT.total_seconds()))) if seconds else None

    total_seconds = 0
    cursor = 0
    matched = False
    for match in _TOKEN_RE.finditer(raw):
        if raw[cursor : match.start()].strip():
            return None
        amount = int(match.group(1))
        unit = _UNIT_SECONDS[match.group(2).lower()]
        total_seconds += amount * unit
        cursor = match.end()
        matched = True
    if not matched or raw[cursor:].strip() or total_seconds <= 0:
        return None
    return timedelta(seconds=min(total_seconds, int(MAX_TIMEOUT.total_seconds())))


def format_duration(delta: timedelta) -> str:
    """Human-readable duration, e.g. '1d 2h 5m'."""
    seconds = max(0, int(delta.total_seconds()))
    if seconds == 0:
        return "0s"
    parts: list[str] = []
    for label, size in (("w", 604800), ("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        if seconds >= size:
            amount, seconds = divmod(seconds, size)
            parts.append(f"{amount}{label}")
    return " ".join(parts)


def format_seconds(seconds: float | None) -> str:
    if not seconds:
        return "0s"
    return format_duration(timedelta(seconds=float(seconds)))
