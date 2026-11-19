from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import discord

from core.settings import get_settings

logger = logging.getLogger(__name__)

MAX_FIELD = 1024


@dataclass(frozen=True)
class LogEvent:
    key: str
    column: str
    label: str
    color: tuple[int, int, int]
    description: str


LOG_EVENTS: dict[str, LogEvent] = {
    "join_leave": LogEvent(
        "join_leave",
        "log_join_leave_channel_id",
        "Join/Leave",
        (87, 242, 135),
        "Member joins and leaves",
    ),
    "message_delete": LogEvent(
        "message_delete",
        "log_message_delete_channel_id",
        "Message Delete",
        (237, 66, 69),
        "Deleted and bulk-deleted messages",
    ),
    "message_edit": LogEvent(
        "message_edit",
        "log_message_edit_channel_id",
        "Message Edit",
        (241, 196, 15),
        "Edited messages",
    ),
    "role_change": LogEvent(
        "role_change",
        "log_role_change_channel_id",
        "Role Change",
        (114, 137, 218),
        "Roles added or removed",
    ),
    "nickname_change": LogEvent(
        "nickname_change",
        "log_nickname_change_channel_id",
        "Nickname Change",
        (155, 89, 182),
        "Member nickname changes",
    ),
    "voice": LogEvent(
        "voice",
        "log_voice_channel_id",
        "Voice Activity",
        (26, 188, 156),
        "Voice join/leave/move events",
    ),
    "moderation": LogEvent(
        "moderation",
        "log_moderation_channel_id",
        "Moderation",
        (231, 76, 60),
        "Moderation actions (also !modlog)",
    ),
    "channel_events": LogEvent(
        "channel_events",
        "log_channel_events_channel_id",
        "Channel Events",
        (230, 126, 34),
        "Channel creation and deletion",
    ),
}


def event_keys() -> list[str]:
    return list(LOG_EVENTS)


def normalize_event(value: str | None) -> LogEvent | None:
    if not value:
        return None
    key = value.strip().lower().replace("-", "_")
    return LOG_EVENTS.get(key)


def event_color(event: LogEvent) -> discord.Color:
    return discord.Color.from_rgb(*event.color)


def truncate(text: str | None, limit: int = MAX_FIELD) -> str:
    if not text:
        return "*(empty)*"
    text = text.strip()
    if not text:
        return "*(empty)*"
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def display_user(user: Any | None) -> str:
    if user is None:
        return "Unknown"
    name = getattr(user, "name", None) or getattr(user, "display_name", None)
    user_id = getattr(user, "id", None)
    if name and user_id:
        return f"{name} ({user_id})"
    if user_id:
        return str(user_id)
    return str(user)


async def resolve_log_channel(
    bot, guild: discord.Guild, event: LogEvent
) -> discord.TextChannel | None:
    """Return the configured log channel for an event, if any."""
    try:
        settings = await get_settings(bot, guild)
    except Exception as exc:  # noqa: BLE001 - logging must never raise
        logger.warning("Failed to load settings for logging: %s", exc)
        return None
    channel_id = settings.get(event.column)
    if not channel_id:
        return None
    channel = guild.get_channel(int(channel_id))
    if channel is None:
        try:
            channel = await guild.fetch_channel(int(channel_id))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None
    return channel if isinstance(channel, discord.TextChannel) else None


async def send_log(
    bot,
    guild: discord.Guild,
    event: LogEvent,
    embed: discord.Embed,
    *,
    activity_type: str | None = None,
    actor_id: int | None = None,
    target_id: int | None = None,
    channel_id: int | None = None,
    payload: dict[str, Any] | None = None,
    store: bool = True,
) -> None:
    """Store an activity log and mirror the embed to the configured channel."""
    channel = await resolve_log_channel(bot, guild, event)
    if store:
        await bot.db.add_activity_log(
            guild.id,
            activity_type or event.key,
            actor_id=actor_id,
            target_id=target_id,
            channel_id=channel_id,
            payload=payload or {},
        )
    if channel is None:
        return
    try:
        await channel.send(embed=embed)
    except discord.HTTPException as exc:
        logger.warning(
            "Failed to send %s log in guild %s: %s", event.key, guild.id, exc
        )
