from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import discord
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

AUTOMATION_TYPES: dict[str, dict[str, Any]] = {
    "announcement": {
        "label": "Scheduled announcement",
        "scheduled": True,
        "description": "Post a message on a cron schedule.",
    },
    "message": {
        "label": "Automated message",
        "scheduled": True,
        "description": "Post a recurring message on a cron schedule.",
    },
    "reminder": {
        "label": "Member reminder",
        "scheduled": True,
        "description": "Post a recurring reminder (role/user mentions allowed).",
    },
    "stats": {
        "label": "Statistics snapshot",
        "scheduled": True,
        "description": "Save a server statistics snapshot, optionally post it.",
    },
    "autorole": {
        "label": "Automatic role assignment",
        "scheduled": False,
        "description": "Give roles to members when they join.",
    },
    "welcome": {
        "label": "Welcome hook",
        "scheduled": False,
        "description": "Send an extra welcome message on join.",
    },
    "goodbye": {
        "label": "Goodbye hook",
        "scheduled": False,
        "description": "Send an extra goodbye message on leave.",
    },
    "response": {
        "label": "Automated response",
        "scheduled": False,
        "description": "Reply when a message contains a trigger phrase.",
    },
}

SCHEDULED_TYPES = frozenset(
    key for key, meta in AUTOMATION_TYPES.items() if meta["scheduled"]
)

CRON_HELP = 'UTC cron with 5 fields, quoted: "0 9 * * *"'


def automation_types() -> list[str]:
    return list(AUTOMATION_TYPES)


def normalize_type(value: str | None) -> str | None:
    if not value:
        return None
    key = value.strip().lower().replace("-", "_")
    key = {"auto_role": "autorole", "auto_roles": "autorole"}.get(key, key)
    return key if key in AUTOMATION_TYPES else None


def is_scheduled(automation_type: str) -> bool:
    return automation_type in SCHEDULED_TYPES


def validate_cron(expression: str | None) -> bool:
    if not expression or not expression.strip():
        return False
    try:
        CronTrigger.from_crontab(expression.strip(), timezone=UTC)
    except (ValueError, TypeError, KeyError):
        return False
    return True


def chunk_message(text: str, limit: int = 2000) -> list[str]:
    """Split text into Discord-safe chunks, preferring newline boundaries."""
    text = (text or "").strip()
    if not text:
        return []
    chunks: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n", 0, limit)
        if split_at <= 0:
            split_at = remaining.rfind(" ", 0, limit)
        if split_at <= 0:
            split_at = limit
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    return chunks


def render_message(
    template: str | None,
    *,
    guild: discord.Guild | None = None,
    member: discord.Member | None = None,
    extra: dict[str, str] | None = None,
) -> str:
    """Replace automation placeholders without str.format KeyErrors."""
    if not template:
        return ""
    replacements = {
        "{guild}": guild.name if guild else "",
        "{member_count}": str(guild.member_count) if guild else "",
        "{user}": getattr(member, "name", "") if member else "",
        "{display_name}": getattr(member, "display_name", "") if member else "",
        "{mention}": member.mention if member else "",
        "{time}": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
    }
    replacements.update(extra or {})
    rendered = template
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    return rendered.strip()


def response_matches(payload: dict[str, Any], content: str) -> bool:
    """Case-insensitive substring match; separate phrases with `|`."""
    trigger = str(payload.get("trigger") or "").strip().lower()
    if not trigger or not content:
        return False
    haystack = content.lower()
    return any(
        phrase.strip() in haystack
        for phrase in trigger.split("|")
        if phrase.strip()
    )
