from __future__ import annotations

import logging
from typing import Any

import discord

from core.settings import get_settings

logger = logging.getLogger(__name__)

ACTION_LABELS = {
    "ban": "Member Banned",
    "unban": "Member Unbanned",
    "kick": "Member Kicked",
    "timeout": "Member Timed Out",
    "untimeout": "Timeout Removed",
    "warn": "Member Warned",
    "unwarn": "Warning Removed",
    "clear": "Messages Cleared",
    "lock": "Channel Locked",
    "unlock": "Channel Unlocked",
    "automod_spam": "Automod: Spam",
    "automod_link": "Automod: Link",
    "automod_invite": "Automod: Invite",
}

ACTION_COLORS = {
    "ban": discord.Color.from_rgb(237, 66, 69),
    "unban": discord.Color.from_rgb(87, 242, 135),
    "kick": discord.Color.from_rgb(230, 126, 34),
    "timeout": discord.Color.from_rgb(241, 196, 15),
    "untimeout": discord.Color.from_rgb(87, 242, 135),
    "warn": discord.Color.from_rgb(254, 231, 92),
    "unwarn": discord.Color.from_rgb(87, 242, 135),
    "clear": discord.Color.from_rgb(114, 137, 218),
    "lock": discord.Color.from_rgb(255, 140, 0),
    "unlock": discord.Color.from_rgb(87, 242, 135),
    "automod_spam": discord.Color.from_rgb(241, 196, 15),
    "automod_link": discord.Color.from_rgb(241, 196, 15),
    "automod_invite": discord.Color.from_rgb(241, 196, 15),
}


def action_label(action: str) -> str:
    return ACTION_LABELS.get(action, action.replace("_", " ").title())


def _display(user: Any) -> str:
    if user is None:
        return "Unknown"
    name = getattr(user, "name", None) or getattr(user, "display_name", None)
    user_id = getattr(user, "id", None)
    if name and user_id:
        return f"{name} ({user_id})"
    if user_id:
        return str(user_id)
    return str(user)


async def record_action(
    bot,
    guild: discord.Guild,
    action: str,
    *,
    target: Any | None = None,
    moderator: Any | None = None,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
    extra_fields: list[tuple[str, str]] | None = None,
) -> dict[str, Any] | None:
    """Persist a moderation action and mirror it to the configured log channel."""
    target_id = getattr(target, "id", None) or (metadata or {}).get("target_id")
    moderator_id = getattr(moderator, "id", None) or (metadata or {}).get("moderator_id")
    reason_text = reason or "No reason provided"

    row = await bot.db.add_moderation_log(
        guild.id,
        action,
        target_id=target_id,
        moderator_id=moderator_id,
        reason=reason_text,
        metadata=metadata or {},
    )
    await bot.db.add_activity_log(
        guild.id,
        "moderation",
        actor_id=moderator_id,
        target_id=target_id,
        channel_id=(metadata or {}).get("channel_id"),
        payload={
            "action": action,
            "reason": reason_text,
            "metadata": metadata or {},
        },
    )

    try:
        settings = await get_settings(bot, guild)
        channel_id = settings.get("log_moderation_channel_id")
        if not channel_id:
            return row
        channel = guild.get_channel(int(channel_id))
        if channel is None:
            channel = await guild.fetch_channel(int(channel_id))
        if not isinstance(channel, discord.TextChannel):
            return row
        embed = discord.Embed(
            title=action_label(action),
            color=ACTION_COLORS.get(action, discord.Color.blurple()),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Target", value=_display(target), inline=True)
        embed.add_field(name="Moderator", value=_display(moderator), inline=True)
        embed.add_field(name="Reason", value=reason_text[:1024], inline=False)
        for name, value in extra_fields or []:
            embed.add_field(name=name, value=value[:1024], inline=True)
        await channel.send(embed=embed)
    except discord.HTTPException as exc:
        logger.warning("Failed to post moderation log for guild %s: %s", guild.id, exc)
    except Exception as exc:  # noqa: BLE001 - logging must never break moderation
        logger.warning("Moderation log error for guild %s: %s", guild.id, exc)
    return row
