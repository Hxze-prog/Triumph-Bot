from __future__ import annotations

import discord


def collect_stats(guild: discord.Guild) -> dict[str, int]:
    """Collect a point-in-time statistics snapshot for a guild."""
    return {
        "member_count": guild.member_count or len(guild.members),
        "human_count": sum(1 for member in guild.members if not member.bot),
        "bot_count": sum(1 for member in guild.members if member.bot),
        "online_count": sum(
            1 for member in guild.members if member.status != discord.Status.offline
        ),
        "channel_count": len(guild.channels),
        "role_count": len(guild.roles),
        "boost_count": guild.premium_subscription_count or 0,
    }


def stats_embed(stats: dict[str, int], *, title: str = "Server Statistics") -> discord.Embed:
    embed = discord.Embed(title=title, color=discord.Color.blurple())
    embed.add_field(name="Members", value=str(stats.get("member_count", 0)), inline=True)
    embed.add_field(name="Humans", value=str(stats.get("human_count", 0)), inline=True)
    embed.add_field(name="Bots", value=str(stats.get("bot_count", 0)), inline=True)
    embed.add_field(name="Online", value=str(stats.get("online_count", 0)), inline=True)
    embed.add_field(name="Channels", value=str(stats.get("channel_count", 0)), inline=True)
    embed.add_field(name="Roles", value=str(stats.get("role_count", 0)), inline=True)
    embed.add_field(name="Boosts", value=str(stats.get("boost_count", 0)), inline=True)
    return embed
