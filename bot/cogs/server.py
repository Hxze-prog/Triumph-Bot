from __future__ import annotations

import logging
from datetime import datetime

import discord
from core.settings import get_settings
from discord.ext import commands
from services.durations import format_seconds, parse_duration
from services.polls import (
    NUMBER_EMOJIS,
    normalize_emoji,
    parse_poll_body,
    poll_embed,
)
from services.server_stats import collect_stats

logger = logging.getLogger(__name__)


def _ts(value: datetime | None) -> str:
    if value is None:
        return "unknown"
    return f"{discord.utils.format_dt(value, 'f')} ({discord.utils.format_dt(value, 'R')})"


def _status_label(member: discord.Member) -> str:
    return {
        discord.Status.online: "online",
        discord.Status.idle: "idle",
        discord.Status.dnd: "do not disturb",
        discord.Status.offline: "offline",
    }.get(member.status, "unknown")


_NAMED_COLORS = {
    "blurple": discord.Color.blurple,
    "blue": discord.Color.blue,
    "green": discord.Color.green,
    "red": discord.Color.red,
    "gold": discord.Color.gold,
    "orange": discord.Color.orange,
    "purple": discord.Color.purple,
    "magenta": discord.Color.magenta,
    "teal": discord.Color.teal,
    "dark_theme": discord.Color.dark_theme,
}


def parse_embed_color(value: str) -> discord.Color | None:
    lowered = value.strip().lower()
    if lowered == "random":
        return discord.Color.random()
    factory = _NAMED_COLORS.get(lowered)
    if factory is not None:
        return factory()
    try:
        return discord.Color.from_str(value.strip())
    except ValueError:
        return None


class Server(commands.Cog, name="Server"):
    """Server/member info, polls, embeds, slowmode, and statistics."""

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(name="userinfo", aliases=["whois"])
    @commands.guild_only()
    async def userinfo(
        self, ctx: commands.Context, member: discord.Member | None = None
    ) -> None:
        """Show information about a member (defaults to you)."""
        target = member or ctx.author
        embed = discord.Embed(
            title=f"User info: {target}",
            color=target.color if target.color.value else discord.Color.blurple(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="ID", value=f"`{target.id}`", inline=True)
        embed.add_field(name="Display name", value=target.display_name, inline=True)
        embed.add_field(name="Bot", value="yes" if target.bot else "no", inline=True)
        embed.add_field(
            name="Account created", value=_ts(target.created_at), inline=False
        )
        embed.add_field(
            name="Joined server",
            value=_ts(target.joined_at) if target.joined_at else "unknown",
            inline=False,
        )
        embed.add_field(name="Status", value=_status_label(target), inline=True)
        top_role = target.top_role.mention if target.top_role else "none"
        embed.add_field(name="Top role", value=top_role, inline=True)
        roles = [role.mention for role in reversed(target.roles) if not role.is_default()]
        embed.add_field(
            name=f"Roles ({len(roles)})",
            value=(", ".join(roles[:15]) + (" ..." if len(roles) > 15 else ""))
            if roles
            else "none",
            inline=False,
        )
        if target.activities:
            activity = target.activities[0]
            name = getattr(activity, "name", None) or str(activity)
            embed.add_field(name="Activity", value=name, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo", aliases=["guildinfo"])
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context) -> None:
        """Show information about this server."""
        guild = ctx.guild
        humans = sum(1 for member in guild.members if not member.bot)
        bots = sum(1 for member in guild.members if member.bot)
        online = sum(
            1 for member in guild.members if member.status != discord.Status.offline
        )
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        embed = discord.Embed(title=guild.name, color=discord.Color.blurple())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(
            name="Owner", value=f"<@{guild.owner_id}>", inline=True
        )
        embed.add_field(
            name="Created", value=_ts(guild.created_at), inline=False
        )
        embed.add_field(
            name="Members",
            value=f"{guild.member_count} total\n{humans} humans / {bots} bots\n{online} online",
            inline=True,
        )
        embed.add_field(
            name="Channels",
            value=f"{text_channels} text\n{voice_channels} voice\n{categories} categories",
            inline=True,
        )
        embed.add_field(
            name="Roles / Boosts",
            value=f"{len(guild.roles)} roles\n{guild.premium_subscription_count} boosts (Tier {guild.premium_tier})",
            inline=True,
        )
        embed.add_field(
            name="Verification",
            value=str(guild.verification_level).title(),
            inline=True,
        )
        await ctx.send(embed=embed)

    @commands.command(name="avatar", aliases=["av"])
    @commands.guild_only()
    async def avatar(
        self, ctx: commands.Context, member: discord.Member | None = None
    ) -> None:
        """Show a member's global and server avatar."""
        target = member or ctx.author
        embed = discord.Embed(
            title=f"Avatar: {target.display_name}",
            color=discord.Color.blurple(),
        )
        embed.set_image(url=target.display_avatar.url)
        embed.add_field(
            name="Global avatar",
            value=f"[link]({target.default_avatar.url})",
            inline=True,
        )
        if target.guild_avatar:
            embed.add_field(
                name="Server avatar",
                value=f"[link]({target.guild_avatar.url})",
                inline=True,
            )
        await ctx.send(embed=embed)

    @commands.command(name="roleinfo")
    @commands.guild_only()
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role) -> None:
        """Show information about a role."""
        embed = discord.Embed(
            title=f"Role info: {role.name}",
            color=role.color if role.color.value else discord.Color.default(),
        )
        embed.add_field(name="ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="Color", value=f"`{role.color}`", inline=True)
        embed.add_field(name="Position", value=str(role.position), inline=True)
        embed.add_field(name="Members", value=str(len(role.members)), inline=True)
        embed.add_field(name="Hoisted", value="yes" if role.hoist else "no", inline=True)
        embed.add_field(
            name="Mentionable", value="yes" if role.mentionable else "no", inline=True
        )
        embed.add_field(
            name="Created", value=_ts(role.created_at), inline=False
        )
        permissions = [name.replace("_", " ").title() for name, value in role.permissions if value]
        embed.add_field(
            name=f"Permissions ({len(permissions)})",
            value=(", ".join(permissions[:20]) + (" ..." if len(permissions) > 20 else ""))
            if permissions
            else "none",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="slowmode", aliases=["slow"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def slowmode(
        self,
        ctx: commands.Context,
        value: str,
        channel: discord.TextChannel | None = None,
    ) -> None:
        """Set channel slowmode (`!slowmode 10s #channel`, `off` to disable)."""
        target = channel or ctx.channel
        lowered = value.strip().lower()
        if lowered in {"off", "none", "0"}:
            seconds = 0
        elif value.isdigit():
            seconds = int(value)
        else:
            delta = parse_duration(value)
            if delta is None:
                await ctx.send("Use seconds or a duration like `10s`, `1m`, or `off`.")
                return
            seconds = int(delta.total_seconds())
        if seconds < 0 or seconds > 21600:
            await ctx.send("Slowmode must be between 0 and 21600 seconds (6 hours).")
            return
        try:
            await target.edit(
                slowmode_delay=seconds,
                reason=f"Slowmode set by {ctx.author} ({ctx.author.id})",
            )
        except discord.Forbidden:
            await ctx.send("I do not have permission to edit that channel.")
            return
        except discord.HTTPException as exc:
            await ctx.send(f"Could not update slowmode: {exc}")
            return
        await ctx.send(
            f"Slowmode for {target.mention} set to {format_seconds(seconds)}."
            if seconds
            else f"Slowmode disabled for {target.mention}."
        )

    @commands.command(name="embed", aliases=["sayembed"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def embed(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        title: str,
        description: str,
        color: str | None = None,
        image_url: str | None = None,
    ) -> None:
        """Post a custom embed. Use quotes for multi-word values.

        Example: `!embed #general "Rules" "Be nice to each other." #5865F2`
        """
        if len(title) > 256 or len(description) > 4096:
            await ctx.send("Title max 256 chars, description max 4096 chars.")
            return
        embed_color = discord.Color.blurple()
        if color:
            parsed = parse_embed_color(color)
            if parsed is None:
                await ctx.send(
                    "Invalid color. Use a hex value like `#5865F2`, a name "
                    "(blurple, red, green, gold, ...), or `random`."
                )
                return
            embed_color = parsed
        embed = discord.Embed(title=title, description=description, color=embed_color)
        if image_url:
            if not image_url.startswith(("http://", "https://")):
                await ctx.send("Image URL must start with http:// or https://.")
                return
            embed.set_image(url=image_url)
        embed.set_footer(text=f"Posted by {ctx.author}")
        try:
            await channel.send(embed=embed)
        except discord.HTTPException as exc:
            await ctx.send(f"Could not post the embed: {exc}")
            return
        await ctx.send(f"Embed posted in {channel.mention}.", delete_after=5)

    @commands.group(name="poll", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def poll(self, ctx: commands.Context, *, body: str = "") -> None:
        """Create a poll: `!poll Question | Option 1 | Option 2 ...` (2-10 options)."""
        if not body.strip():
            await ctx.send(
                "Usage: `!poll Question | Option 1 | Option 2 ...` (2-10 options).\n"
                "Also: `!poll results <message_id>` and `!poll end <message_id>`."
            )
            return
        try:
            question, options = parse_poll_body(body)
        except ValueError as exc:
            await ctx.send(str(exc))
            return
        await get_settings(self.bot, ctx.guild)
        message = await ctx.send(embed=poll_embed(question, options, str(ctx.author)))
        for index in range(len(options)):
            try:
                await message.add_reaction(NUMBER_EMOJIS[index])
            except discord.HTTPException:
                logger.warning("Failed to add poll reaction %s", index)
        row = await self.bot.db.create_poll(
            ctx.guild.id,
            ctx.channel.id,
            question,
            options,
            created_by=ctx.author.id,
        )
        if row is None:
            await ctx.send(
                "Poll posted, but it could not be saved to the database (results still work)."
            )
        else:
            await self.bot.db.set_poll_message(
                ctx.guild.id, int(row["id"]), message.id
            )

    async def _poll_counts(
        self,
        guild: discord.Guild,
        channel_id: int,
        message_id: int,
        fallback_options: list[str] | None = None,
    ) -> tuple[list[str], list[int], str | None]:
        channel = guild.get_channel(channel_id)
        if channel is None:
            return [], [], "channel not found"
        if not isinstance(channel, discord.TextChannel):
            return [], [], "not a text channel"
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return [], [], "message not found"
        except discord.HTTPException as exc:
            return [], [], f"fetch failed: {exc}"
        counts = {
            normalize_emoji(str(reaction.emoji)): reaction.count
            for reaction in message.reactions
        }
        options = fallback_options or []
        if not options:
            fallback_count = sum(
                1
                for emoji in NUMBER_EMOJIS
                if normalize_emoji(emoji) in counts
            )
            options = [f"Option {index + 1}" for index in range(fallback_count)]
        tallies = [
            max(0, counts.get(normalize_emoji(NUMBER_EMOJIS[index]), 0) - 1)
            for index in range(len(options[: len(NUMBER_EMOJIS)]))
        ]
        return options, tallies, None

    @poll.command(name="results")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def poll_results(self, ctx: commands.Context, message_id: int) -> None:
        """Show live results for a poll message in this channel."""
        record = await self.bot.db.get_poll(ctx.guild.id, message_id)
        fallback = list(record.get("options") or []) if record else None
        options, tallies, error = await self._poll_counts(
            ctx.guild, ctx.channel.id, message_id, fallback
        )
        if error:
            await ctx.send(f"Could not load poll results: {error}.")
            return
        embed = self._results_embed(
            record.get("question") if record else "Poll results", options, tallies
        )
        if record and record.get("closed"):
            embed.set_footer(text="Poll closed")
        await ctx.send(embed=embed)

    @poll.command(name="end")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def poll_end(self, ctx: commands.Context, message_id: int) -> None:
        """Close a poll and post its final results."""
        record = await self.bot.db.get_poll(ctx.guild.id, message_id)
        if record is None:
            await ctx.send("That poll is not tracked in the database.")
            return
        updated = await self.bot.db.close_poll(ctx.guild.id, message_id)
        if updated is None:
            await ctx.send("Could not close the poll.")
            return
        options, tallies, error = await self._poll_counts(
            ctx.guild, int(record["channel_id"]), message_id, list(record.get("options") or [])
        )
        if error:
            await ctx.send(f"Poll closed, but results could not be loaded: {error}.")
            return
        embed = self._results_embed(record.get("question") or "Poll results", options, tallies)
        embed.set_footer(text="Poll closed")
        await ctx.send(embed=embed)

    @staticmethod
    def _results_embed(
        question: str | None, options: list[str], tallies: list[int]
    ) -> discord.Embed:
        total = sum(tallies)
        embed = discord.Embed(title=f"Results: {question or 'Poll'}", color=discord.Color.green())
        lines = []
        for index, option in enumerate(options):
            votes = tallies[index] if index < len(tallies) else 0
            percent = (votes / total * 100) if total else 0
            lines.append(f"{NUMBER_EMOJIS[index] if index < len(NUMBER_EMOJIS) else ''} {option} - **{votes}** ({percent:.0f}%)")
        embed.description = "\n".join(lines) or "No options recorded."
        embed.set_footer(text=f"Total votes: {total}")
        return embed

    @commands.group(name="serverstats", aliases=["stats"], invoke_without_command=True)
    @commands.guild_only()
    async def serverstats(self, ctx: commands.Context) -> None:
        """Show live server statistics and store a snapshot."""
        stats = collect_stats(ctx.guild)
        await get_settings(self.bot, ctx.guild)
        await self.bot.db.add_server_stats(ctx.guild.id, stats)
        embed = discord.Embed(title=f"Statistics: {ctx.guild.name}", color=discord.Color.blurple())
        embed.add_field(name="Members", value=str(stats["member_count"]), inline=True)
        embed.add_field(name="Humans", value=str(stats["human_count"]), inline=True)
        embed.add_field(name="Bots", value=str(stats["bot_count"]), inline=True)
        embed.add_field(name="Online", value=str(stats["online_count"]), inline=True)
        embed.add_field(name="Channels", value=str(stats["channel_count"]), inline=True)
        embed.add_field(name="Roles", value=str(stats["role_count"]), inline=True)
        embed.add_field(name="Boosts", value=str(stats["boost_count"]), inline=True)
        embed.set_footer(text="Snapshot saved to Supabase")
        await ctx.send(embed=embed)

    @serverstats.command(name="history")
    @commands.guild_only()
    async def serverstats_history(
        self, ctx: commands.Context, limit: int = 5
    ) -> None:
        """Show recent saved statistics snapshots."""
        limit = max(1, min(limit, 20))
        rows = await self.bot.db.list_server_stats(ctx.guild.id, limit=limit)
        embed = discord.Embed(title="Statistics history", color=discord.Color.blurple())
        if not rows:
            embed.description = "No snapshots recorded yet."
        else:
            for row in rows:
                recorded = row.get("recorded_at")
                stamp = "unknown"
                if recorded:
                    try:
                        stamp = discord.utils.format_dt(
                            datetime.fromisoformat(str(recorded)), "R"
                        )
                    except ValueError:
                        stamp = str(recorded)
                embed.add_field(
                    name=stamp,
                    value=(
                        f"members {row.get('member_count')}, humans {row.get('human_count')}, "
                        f"bots {row.get('bot_count')}, online {row.get('online_count')}, "
                        f"channels {row.get('channel_count')}, boosts {row.get('boost_count')}"
                    ),
                    inline=False,
                )
        await ctx.send(embed=embed)


async def setup(bot) -> None:
    await bot.add_cog(Server(bot))
