from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands

from core.permissions import mod_or_admin
from core.settings import get_settings, save_settings
from services.activity_log import (
    LOG_EVENTS,
    display_user,
    event_color,
    event_keys,
    normalize_event,
    send_log,
    truncate,
)

logger = logging.getLogger(__name__)


def _format_ts(value: Any) -> str:
    if not value:
        return "unknown"
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return str(value)
    return discord.utils.format_dt(parsed, "R")


def _payload_preview(payload: dict[str, Any]) -> str:
    for key in ("content", "message", "before", "after", "reason"):
        value = payload.get(key)
        if value:
            return truncate(str(value), 120)
    roles = payload.get("roles_added") or payload.get("roles_removed")
    if roles:
        return truncate(", ".join(str(role) for role in roles), 120)
    action = payload.get("action")
    if action:
        return str(action)
    return ""


class Logging(commands.Cog, name="Logging"):
    """Per-event audit logging to Discord channels and Supabase."""

    def __init__(self, bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Member events
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.guild is None:
            return
        embed = discord.Embed(
            title="Member Joined",
            description=f"{member.mention} ({display_user(member)})",
            color=event_color(LOG_EVENTS["join_leave"]),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="Account created",
            value=discord.utils.format_dt(member.created_at, "R"),
            inline=True,
        )
        embed.add_field(name="Members", value=str(member.guild.member_count), inline=True)
        if member.bot:
            embed.add_field(name="Bot", value="yes", inline=True)
        await send_log(
            self.bot,
            member.guild,
            LOG_EVENTS["join_leave"],
            embed,
            target_id=member.id,
            payload={
                "action": "join",
                "username": member.name,
                "member_count": member.guild.member_count,
                "bot": member.bot,
            },
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        if member.guild is None:
            return
        embed = discord.Embed(
            title="Member Left",
            description=f"{display_user(member)}",
            color=discord.Color.from_rgb(237, 66, 69),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        if member.joined_at:
            embed.add_field(
                name="Joined",
                value=discord.utils.format_dt(member.joined_at, "R"),
                inline=True,
            )
        embed.add_field(name="Members", value=str(member.guild.member_count), inline=True)
        await send_log(
            self.bot,
            member.guild,
            LOG_EVENTS["join_leave"],
            embed,
            target_id=member.id,
            payload={
                "action": "leave",
                "username": member.name,
                "member_count": member.guild.member_count,
            },
        )

    # ------------------------------------------------------------------
    # Message events
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot:
            return
        embed = discord.Embed(
            title="Message Deleted",
            description=f"Message by {message.author.mention} in {message.channel.mention}",
            color=event_color(LOG_EVENTS["message_delete"]),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Author", value=display_user(message.author), inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Content", value=truncate(message.content), inline=False)
        if message.attachments:
            names = ", ".join(attachment.filename for attachment in message.attachments)
            embed.add_field(name="Attachments", value=truncate(names), inline=False)
        embed.set_footer(text=f"Message ID: {message.id}")
        await send_log(
            self.bot,
            message.guild,
            LOG_EVENTS["message_delete"],
            embed,
            actor_id=message.author.id,
            channel_id=message.channel.id,
            payload={
                "content": truncate(message.content, 1900),
                "message_id": message.id,
                "attachments": [a.filename for a in message.attachments],
            },
        )

    @commands.Cog.listener()
    async def on_bulk_message_delete(
        self, messages: list[discord.Message]
    ) -> None:
        if not messages:
            return
        guild = messages[0].guild
        if guild is None:
            return
        channel = messages[0].channel
        authors = {display_user(message.author) for message in messages}
        embed = discord.Embed(
            title="Bulk Messages Deleted",
            description=f"**{len(messages)}** messages removed in {channel.mention}",
            color=event_color(LOG_EVENTS["message_delete"]),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name="Authors",
            value=truncate(", ".join(sorted(authors)[:15]), 500),
            inline=False,
        )
        await send_log(
            self.bot,
            guild,
            LOG_EVENTS["message_delete"],
            embed,
            channel_id=channel.id,
            payload={"count": len(messages), "channel": channel.name},
        )

    @commands.Cog.listener()
    async def on_message_edit(
        self, before: discord.Message, after: discord.Message
    ) -> None:
        if (
            before.guild is None
            or before.author.bot
            or before.content == after.content
        ):
            return
        embed = discord.Embed(
            title="Message Edited",
            description=f"Message by {before.author.mention} in {before.channel.mention}",
            color=event_color(LOG_EVENTS["message_edit"]),
            timestamp=discord.utils.utcnow(),
            url=after.jump_url,
        )
        embed.add_field(name="Author", value=display_user(before.author), inline=True)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Before", value=truncate(before.content), inline=False)
        embed.add_field(name="After", value=truncate(after.content), inline=False)
        await send_log(
            self.bot,
            before.guild,
            LOG_EVENTS["message_edit"],
            embed,
            actor_id=before.author.id,
            channel_id=before.channel.id,
            payload={
                "message_id": before.id,
                "before": truncate(before.content, 900),
                "after": truncate(after.content, 900),
            },
        )

    # ------------------------------------------------------------------
    # Member update (roles / nickname)
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_member_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        if before.guild is None:
            return
        added = [role for role in after.roles if role not in before.roles]
        removed = [role for role in before.roles if role not in after.roles]
        if added or removed:
            embed = discord.Embed(
                title="Roles Updated",
                description=display_user(after),
                color=event_color(LOG_EVENTS["role_change"]),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(
                name="Added",
                value=truncate(" ".join(role.mention for role in added), 600),
                inline=False,
            )
            embed.add_field(
                name="Removed",
                value=truncate(" ".join(role.mention for role in removed), 600),
                inline=False,
            )
            await send_log(
                self.bot,
                before.guild,
                LOG_EVENTS["role_change"],
                embed,
                target_id=after.id,
                payload={
                    "roles_added": [role.name for role in added],
                    "roles_removed": [role.name for role in removed],
                },
            )

        if before.nick != after.nick:
            embed = discord.Embed(
                title="Nickname Changed",
                description=display_user(after),
                color=event_color(LOG_EVENTS["nickname_change"]),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(
                name="Before",
                value=truncate(before.nick or before.name, 200),
                inline=True,
            )
            embed.add_field(
                name="After",
                value=truncate(after.nick or after.name, 200),
                inline=True,
            )
            await send_log(
                self.bot,
                before.guild,
                LOG_EVENTS["nickname_change"],
                embed,
                target_id=after.id,
                payload={"before": before.nick, "after": after.nick},
            )

    # ------------------------------------------------------------------
    # Voice events
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.bot or before.channel == after.channel:
            return
        if before.channel is None:
            action = "joined"
            color = discord.Color.from_rgb(87, 242, 135)
        elif after.channel is None:
            action = "left"
            color = discord.Color.from_rgb(237, 66, 69)
        else:
            action = "moved"
            color = event_color(LOG_EVENTS["voice"])
        embed = discord.Embed(
            title=f"Voice {action.title()}",
            description=display_user(member),
            color=color,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name="From",
            value=before.channel.mention if before.channel else "none",
            inline=True,
        )
        embed.add_field(
            name="To",
            value=after.channel.mention if after.channel else "none",
            inline=True,
        )
        await send_log(
            self.bot,
            member.guild,
            LOG_EVENTS["voice"],
            embed,
            target_id=member.id,
            channel_id=(
                after.channel.id if after.channel else before.channel.id
            ),
            payload={
                "action": action,
                "from": before.channel.name if before.channel else None,
                "to": after.channel.name if after.channel else None,
            },
        )

    # ------------------------------------------------------------------
    # Channel events
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_guild_channel_create(
        self, channel: discord.abc.GuildChannel
    ) -> None:
        await self._channel_event(channel, "created")

    @commands.Cog.listener()
    async def on_guild_channel_delete(
        self, channel: discord.abc.GuildChannel
    ) -> None:
        await self._channel_event(channel, "deleted")

    async def _channel_event(
        self, channel: discord.abc.GuildChannel, action: str
    ) -> None:
        guild = channel.guild
        category = getattr(channel, "category", None)
        embed = discord.Embed(
            title=f"Channel {action.title()}",
            description=f"**{truncate(channel.name, 200)}** ({channel.type})",
            color=event_color(LOG_EVENTS["channel_events"]),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Channel ID", value=str(channel.id), inline=True)
        embed.add_field(
            name="Category",
            value=category.name if category else "none",
            inline=True,
        )
        await send_log(
            self.bot,
            guild,
            LOG_EVENTS["channel_events"],
            embed,
            channel_id=channel.id,
            payload={
                "action": action,
                "name": channel.name,
                "type": str(channel.type),
                "category": category.name if category else None,
            },
        )

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    @commands.group(
        name="logs", aliases=["logging"], invoke_without_command=True
    )
    @commands.guild_only()
    async def logs(self, ctx: commands.Context) -> None:
        """Configure audit logging channels."""
        await self._send_status(ctx)

    async def _send_status(self, ctx: commands.Context) -> None:
        settings = await get_settings(self.bot, ctx.guild)
        embed = discord.Embed(
            title="Logging channels",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        for event in LOG_EVENTS.values():
            channel_id = settings.get(event.column)
            embed.add_field(
                name=event.label,
                value=f"<#{channel_id}>" if channel_id else "not set",
                inline=True,
            )
        embed.set_footer(
            text="Set with !logs set <event> #channel | Turn off with !logs set <event> off"
        )
        await ctx.send(embed=embed)

    @logs.command(name="status")
    @commands.guild_only()
    async def status(self, ctx: commands.Context) -> None:
        """Show the configured channel for each log event."""
        await self._send_status(ctx)

    @logs.command(name="set")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def set_channel(
        self,
        ctx: commands.Context,
        event: str,
        channel: discord.TextChannel | str | None = None,
    ) -> None:
        """Set the channel for an event, or `off` to disable it."""
        parsed = normalize_event(event)
        if parsed is None:
            await ctx.send(
                "Unknown event. Choose from: " + ", ".join(event_keys())
            )
            return
        target: int | None
        if channel is None:
            target = ctx.channel.id
        elif isinstance(channel, discord.TextChannel):
            target = channel.id
        elif channel.strip().lower() in {"off", "none", "disable", "disabled"}:
            target = None
        else:
            await ctx.send(
                "Provide a text channel mention/name, or `off` to disable."
            )
            return
        row = await save_settings(self.bot, ctx.guild, {parsed.column: target})
        if row is None:
            await ctx.send("Could not save logging settings (database unavailable).")
            return
        await ctx.send(
            f"{parsed.label} logs disabled."
            if target is None
            else f"{parsed.label} logs will be sent to <#{target}>."
        )

    @logs.command(name="history")
    @commands.guild_only()
    @mod_or_admin()
    async def history(
        self, ctx: commands.Context, event: str | None = None, limit: int = 10
    ) -> None:
        """Show recent stored activity logs (`!logs history [event] [limit]`)."""
        event_type = None
        if event:
            parsed = normalize_event(event)
            if parsed is None:
                await ctx.send(
                    "Unknown event. Choose from: " + ", ".join(event_keys())
                )
                return
            event_type = parsed.key
        limit = max(1, min(limit, 25))
        rows = await self.bot.db.list_activity_logs(
            ctx.guild.id, event_type=event_type, limit=limit
        )
        if not rows:
            await ctx.send("No activity logs found.")
            return
        lines = []
        for row in rows:
            preview = _payload_preview(row.get("payload") or {})
            line = (
                f"`#{row.get('id')}` {_format_ts(row.get('created_at'))} "
                f"**{row.get('event_type')}**"
            )
            if row.get("target_id"):
                line += f" -> <@{row['target_id']}>"
            if preview:
                line += f": {preview}"
            lines.append(line)
        embed = discord.Embed(
            title="Recent activity logs",
            description="\n".join(lines)[:4000],
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        await ctx.send(embed=embed)

    @logs.command(name="test")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def test(self, ctx: commands.Context, event: str) -> None:
        """Send a test log to the configured channel for an event."""
        parsed = normalize_event(event)
        if parsed is None:
            await ctx.send(
                "Unknown event. Choose from: " + ", ".join(event_keys())
            )
            return
        settings = await get_settings(self.bot, ctx.guild)
        if not settings.get(parsed.column):
            await ctx.send(f"{parsed.label} logging is not configured yet.")
            return
        embed = discord.Embed(
            title=f"Test: {parsed.label}",
            description="This is a test log entry.",
            color=event_color(parsed),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Event", value=parsed.key, inline=True)
        embed.add_field(name="Requested by", value=display_user(ctx.author), inline=True)
        await send_log(
            self.bot,
            ctx.guild,
            parsed,
            embed,
            actor_id=ctx.author.id,
            store=False,
        )
        await ctx.send(f"Sent a test {parsed.label} log.", delete_after=5)


async def setup(bot) -> None:
    await bot.add_cog(Logging(bot))
