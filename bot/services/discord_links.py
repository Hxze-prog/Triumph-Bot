from __future__ import annotations

import re

import discord

_MESSAGE_LINK_RE = re.compile(
    r"https?://(?:www\.|ptb\.|canary\.)?discord(?:app)?\.com/channels/"
    r"(\d+|@me)/(\d+)/(\d+)",
    re.IGNORECASE,
)


def parse_emoji(value: str) -> discord.PartialEmoji | None:
    """Accept unicode emoji, `name:id`, or `<:name:id>` / `<a:name:id>`."""
    if not value or not value.strip():
        return None
    return discord.PartialEmoji.from_str(value.strip())


def parse_message_link(value: str) -> tuple[int | None, int, int] | None:
    """Parse a Discord message link into (guild_id, channel_id, message_id).

    guild_id is None for @me links.
    """
    if not value:
        return None
    match = _MESSAGE_LINK_RE.search(value.strip())
    if match is None:
        return None
    guild_raw, channel_id, message_id = match.groups()
    guild_id = None if guild_raw == "@me" else int(guild_raw)
    return guild_id, int(channel_id), int(message_id)


def emoji_key(emoji) -> str:
    """Stable DB key for a unicode/custom PartialEmoji (str preserves animated form)."""
    return str(emoji)
