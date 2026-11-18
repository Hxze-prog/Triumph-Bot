from __future__ import annotations

import logging
from typing import Any

import discord

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 30.0


async def get_settings(bot, guild: discord.Guild) -> dict[str, Any]:
    """Return guild_settings, creating guild/settings rows on first use."""
    cached = bot.settings_cache.get(guild.id)
    if isinstance(cached, dict) and cached:
        return cached

    row = await bot.db.get_guild_settings(guild.id)
    if row is None:
        await bot.db.upsert_guild(
            guild.id,
            name=guild.name,
            icon_url=guild.icon.url if guild.icon else None,
            owner_id=guild.owner_id,
        )
        row = await bot.db.upsert_guild_settings(guild.id, {})
    if row:
        bot.settings_cache.set(guild.id, row, ttl=CACHE_TTL_SECONDS)
        return row
    logger.warning("guild_settings unavailable for guild %s (DB/schema issue?)", guild.id)
    return {}


async def save_settings(
    bot, guild: discord.Guild, values: dict[str, Any]
) -> dict[str, Any] | None:
    """Persist guild_settings values and refresh the cache."""
    await get_settings(bot, guild)
    row = await bot.db.upsert_guild_settings(guild.id, values)
    if row:
        bot.settings_cache.set(guild.id, row, ttl=CACHE_TTL_SECONDS)
    return row
