from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

PLACEHOLDERS = (
    "user",
    "mention",
    "name",
    "display_name",
    "server",
    "member_count",
    "member_number",
    "created_at",
    "joined_at",
    "account_age",
    "server_age",
)

DEFAULT_WELCOME_MESSAGE = (
    "Welcome {user} to **{server}**! You are member #{member_number}."
)
DEFAULT_BANNER_TEMPLATE = "You are member #{member_number}"
DEFAULT_GOODBYE_MESSAGE = "**{name}** left **{server}**. We now have {member_count} members."


def format_date(value: Any) -> str:
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=UTC)
        return dt.astimezone(UTC).strftime("%b %d, %Y")
    return "unknown"


def parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def humanize_delta(delta: timedelta) -> str:
    seconds = max(int(delta.total_seconds()), 0)
    units = (
        ("year", 365 * 24 * 3600),
        ("month", 30 * 24 * 3600),
        ("day", 24 * 3600),
        ("hour", 3600),
        ("minute", 60),
    )
    for name, duration in units:
        value = seconds // duration
        if value >= 1:
            return f"{value} {name}{'s' if value != 1 else ''}"
    return "less than a minute"


def age_since(value: Any, *, now: datetime | None = None) -> str:
    dt = parse_datetime(value)
    if dt is None:
        return "unknown"
    current = now or datetime.now(UTC)
    return humanize_delta(current - dt)


def member_context(
    member: Any,
    *,
    member_number: int | None = None,
    now: datetime | None = None,
) -> dict[str, str]:
    """Build placeholder values from a discord.Member (or test double)."""
    guild = getattr(member, "guild", None)
    current = now or datetime.now(UTC)
    display_name = getattr(member, "display_name", None) or getattr(member, "name", "") or "member"

    joined_at = getattr(member, "joined_at", None)
    created_at = getattr(member, "created_at", None)
    member_count = getattr(guild, "member_count", None)
    if member_count is None:
        try:
            member_count = len(guild.members)
        except (AttributeError, TypeError):
            member_count = None

    number = str(member_number) if member_number is not None else "?"

    return {
        "user": getattr(member, "mention", display_name),
        "mention": getattr(member, "mention", display_name),
        "name": getattr(member, "name", display_name),
        "display_name": display_name,
        "server": getattr(guild, "name", "the server"),
        "member_count": str(member_count) if member_count is not None else "?",
        "member_number": number,
        "created_at": format_date(created_at),
        "joined_at": format_date(joined_at),
        "account_age": age_since(created_at, now=current),
        "server_age": age_since(joined_at, now=current),
    }


def render(template: str | None, context: dict[str, str]) -> str:
    """Replace known {placeholders}; unknown placeholders are left untouched."""
    if not template:
        return ""
    out = template
    for key in PLACEHOLDERS:
        if "{" + key + "}" in out and key in context:
            out = out.replace("{" + key + "}", context[key])
    return out
