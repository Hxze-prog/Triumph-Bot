from __future__ import annotations

import logging
from datetime import datetime

import discord
from core.permissions import mod_or_admin
from core.settings import get_settings, save_settings
from discord.ext import commands
from services.durations import format_duration, parse_duration
from services.modlog import action_label, record_action

logger = logging.getLogger(__name__)

NO_REASON = "No reason provided"
MAX_CLEAR = 500
MAX_HISTORY = 25


def _audit_reason(ctx: commands.Context, reason: str) -> str:
    return f"{ctx.author} ({ctx.author.id}): {reason}"


def _format_ts(value: object) -> str:
    if not value:
        return "unknown"
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return str(value)
    if parsed.tzinfo is None:
        return parsed.strftime("%Y-%m-%d %H:%M")
    return discord.utils.format_dt(parsed, "R")


class Moderation(commands.Cog, name="Moderation"):
    """Ban, kick, timeout, warnings, purge, channel locks, and mod history."""

    def __init__(self, bot) -> None:
        self.bot = bot

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        if ctx.guild is not None:
            await get_settings(self.bot, ctx.guild)

    @staticmethod
    async def _notify(
        user: discord.abc.User | None,
        *,
        title: str,
        description: str,
        color: discord.Color,
    ) -> None:
        if user is None or user.bot:
            return
        try:
            embed = discord.Embed(title=title, description=description, color=color)
            embed.set_footer(text="Triumph Bot")
            await user.send(embed=embed)
        except discord.HTTPException:
            pass

    def _hierarchy_error(
        self, ctx: commands.Context, target: discord.Member
    ) -> str | None:
        if target.id == ctx.author.id:
            return "You cannot moderate yourself."
        if target.id == ctx.guild.owner_id:
            return "You cannot moderate the server owner."
        author = (
            ctx.author
            if isinstance(ctx.author, discord.Member)
            else ctx.guild.get_member(ctx.author.id)
        )
        if (
            author is not None
            and author.id != ctx.guild.owner_id
            and target.top_role >= author.top_role
        ):
            return "That member's top role is not below your highest role."
        me = ctx.guild.me
        if me is not None and target.top_role >= me.top_role:
            return "That member's top role is not below mine; move my role higher."
        return None

    async def _confirm(
        self,
        ctx: commands.Context,
        *,
        text: str,
        color: discord.Color | None = None,
    ) -> None:
        await ctx.send(
            embed=discord.Embed(
                description=text, color=color or discord.Color.green()
            )
        )

    @commands.command(name="ban")
    @commands.guild_only()
    @mod_or_admin()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.User,
        *,
        reason: str = NO_REASON,
    ) -> None:
        """Ban a member (or a user ID) with an optional reason."""
        target: discord.Member | None = ctx.guild.get_member(member.id)
        if target is not None:
            error = self._hierarchy_error(ctx, target)
            if error:
                await ctx.send(f"{error}")
                return
            await self._notify(
                target,
                title=f"You were banned from {ctx.guild.name}",
                description=f"Reason: {reason}",
                color=discord.Color.red(),
            )
        try:
            await ctx.guild.ban(
                member,
                reason=_audit_reason(ctx, reason),
                delete_message_seconds=0,
            )
        except discord.Forbidden:
            await ctx.send("I do not have permission to ban that member.")
            return
        except discord.HTTPException as exc:
            await ctx.send(f"Ban failed: {exc}")
            return
        await record_action(
            self.bot,
            ctx.guild,
            "ban",
            target=member,
            moderator=ctx.author,
            reason=reason,
        )
        await self._confirm(
            ctx,
            text=f"Banned **{member}** (`{member.id}`). Reason: {reason}",
            color=discord.Color.red(),
        )

    @commands.command(name="unban")
    @commands.guild_only()
    @mod_or_admin()
    @commands.has_guild_permissions(ban_members=True)
    async def unban(
        self,
        ctx: commands.Context,
        user_id: int,
        *,
        reason: str = NO_REASON,
    ) -> None:
        """Unban a user by ID."""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=_audit_reason(ctx, reason))
        except discord.NotFound:
            await ctx.send("That user is not banned or does not exist.")
            return
        except discord.Forbidden:
            await ctx.send("I do not have permission to unban that user.")
            return
        except discord.HTTPException as exc:
            await ctx.send(f"Unban failed: {exc}")
            return
        await record_action(
            self.bot,
            ctx.guild,
            "unban",
            target=user,
            moderator=ctx.author,
            reason=reason,
        )
        await self._confirm(
            ctx, text=f"Unbanned **{user}** (`{user.id}`). Reason: {reason}"
        )

    @commands.command(name="kick")
    @commands.guild_only()
    @mod_or_admin()
    @commands.has_guild_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = NO_REASON,
    ) -> None:
        """Kick a member with an optional reason."""
        error = self._hierarchy_error(ctx, member)
        if error:
            await ctx.send(f"{error}")
            return
        await self._notify(
            member,
            title=f"You were kicked from {ctx.guild.name}",
            description=f"Reason: {reason}",
            color=discord.Color.orange(),
        )
        try:
            await member.kick(reason=_audit_reason(ctx, reason))
        except discord.Forbidden:
            await ctx.send("I do not have permission to kick that member.")
            return
        except discord.HTTPException as exc:
            await ctx.send(f"Kick failed: {exc}")
            return
        await record_action(
            self.bot,
            ctx.guild,
            "kick",
            target=member,
            moderator=ctx.author,
            reason=reason,
        )
        await self._confirm(
            ctx,
            text=f"Kicked **{member}** (`{member.id}`). Reason: {reason}",
            color=discord.Color.orange(),
        )

    @commands.command(name="timeout", aliases=["mute"])
    @commands.guild_only()
    @mod_or_admin()
    @commands.has_guild_permissions(moderate_members=True)
    async def timeout(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        reason: str = NO_REASON,
    ) -> None:
        """Timeout a member for a duration (examples: 10m, 1h30m, 2d)."""
        delta = parse_duration(duration)
        if delta is None:
            await ctx.send(
                "Invalid duration. Use formats like `10m`, `1h30m`, or `2d` (max 28d)."
            )
            return
        error = self._hierarchy_error(ctx, member)
        if error:
            await ctx.send(f"{error}")
            return
        await self._notify(
            member,
            title=f"You were timed out in {ctx.guild.name}",
            description=f"Duration: {format_duration(delta)}\nReason: {reason}",
            color=discord.Color.gold(),
        )
        try:
            await member.timeout(delta, reason=_audit_reason(ctx, reason))
        except discord.Forbidden:
            await ctx.send("I do not have permission to timeout that member.")
            return
        except discord.HTTPException as exc:
            await ctx.send(f"Timeout failed: {exc}")
            return
        await record_action(
            self.bot,
            ctx.guild,
            "timeout",
            target=member,
            moderator=ctx.author,
            reason=reason,
            metadata={"duration_seconds": int(delta.total_seconds())},
            extra_fields=[("Duration", format_duration(delta))],
        )
        await self._confirm(
            ctx,
            text=(
                f"Timed out **{member}** (`{member.id}`) for "
                f"{format_duration(delta)}. Reason: {reason}"
            ),
            color=discord.Color.gold(),
        )

    @commands.command(name="untimeout", aliases=["unmute"])
    @commands.guild_only()
    @mod_or_admin()
    @commands.has_guild_permissions(moderate_members=True)
    async def untimeout(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = NO_REASON,
    ) -> None:
        """Remove an active timeout."""
        try:
            await member.timeout(None, reason=_audit_reason(ctx, reason))
        except discord.Forbidden:
            await ctx.send("I do not have permission to remove that timeout.")
            return
        except discord.HTTPException as exc:
            await ctx.send(f"Timeout removal failed: {exc}")
            return
        await record_action(
            self.bot,
            ctx.guild,
            "untimeout",
            target=member,
            moderator=ctx.author,
            reason=reason,
        )
        await self._confirm(ctx, text=f"Removed timeout for **{member}**.")

    @commands.command(name="warn")
    @commands.guild_only()
    @mod_or_admin()
    async def warn(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = NO_REASON,
    ) -> None:
        """Warn a member and store the warning in Supabase."""
        error = self._hierarchy_error(ctx, member)
        if error:
            await ctx.send(f"{error}")
            return
        warning = await self.bot.db.add_warning(
            ctx.guild.id, member.id, ctx.author.id, reason
        )
        if warning is None:
            await ctx.send("Could not save the warning (database unavailable).")
            return
        await self._notify(
            member,
            title=f"You received a warning in {ctx.guild.name}",
            description=f"Reason: {reason}\nWarning ID: `{warning.get('id')}`",
            color=discord.Color.gold(),
        )
        active = await self.bot.db.count_active_warnings(ctx.guild.id, member.id)
        await record_action(
            self.bot,
            ctx.guild,
            "warn",
            target=member,
            moderator=ctx.author,
            reason=reason,
            metadata={
                "warning_id": warning.get("id"),
                "active_warnings": active,
            },
            extra_fields=[("Active warnings", str(active))],
        )
        await self._confirm(
            ctx,
            text=(
                f"Warned **{member}** (`{member.id}`). "
                f"Warning `#{warning.get('id')}`, active total: {active}.\nReason: {reason}"
            ),
            color=discord.Color.gold(),
        )

    @commands.command(name="warnings", aliases=["warns"])
    @commands.guild_only()
    @mod_or_admin()
    async def warnings(
        self, ctx: commands.Context, member: discord.Member
    ) -> None:
        """List a member's active warnings."""
        rows = await self.bot.db.list_warnings(
            ctx.guild.id, member.id, active_only=True, limit=MAX_HISTORY
        )
        embed = discord.Embed(
            title=f"Warnings for {member}",
            color=discord.Color.gold(),
        )
        if not rows:
            embed.description = "No active warnings."
        else:
            for row in rows[:MAX_HISTORY]:
                moderator = row.get("moderator_id")
                embed.add_field(
                    name=f"#{row.get('id')} • {_format_ts(row.get('created_at'))}",
                    value=(
                        f"{row.get('reason') or NO_REASON}\n"
                        f"by <@{moderator}>" if moderator else
                        f"{row.get('reason') or NO_REASON}\nby unknown"
                    ),
                    inline=False,
                )
        embed.set_footer(text=f"Active warnings: {len(rows)}")
        await ctx.send(embed=embed)

    @commands.command(name="unwarn")
    @commands.guild_only()
    @mod_or_admin()
    async def unwarn(
        self,
        ctx: commands.Context,
        member: discord.Member,
        warning: str,
    ) -> None:
        """Deactivate a warning: `!unwarn @member <id|latest>`."""
        if warning.lower() == "latest":
            rows = await self.bot.db.list_warnings(
                ctx.guild.id, member.id, active_only=True, limit=1
            )
            if not rows:
                await ctx.send("That member has no active warnings.")
                return
            warning_id = int(rows[0]["id"])
        else:
            try:
                warning_id = int(warning.lstrip("#"))
            except ValueError:
                await ctx.send("Provide a warning ID or `latest`.")
                return
        row = await self.bot.db.get_warning(ctx.guild.id, warning_id)
        if row is None or int(row.get("user_id", 0)) != member.id:
            await ctx.send("That warning does not belong to this member.")
            return
        if not row.get("active"):
            await ctx.send("That warning is already inactive.")
            return
        updated = await self.bot.db.deactivate_warning(ctx.guild.id, warning_id)
        if updated is None:
            await ctx.send("Could not update the warning (database unavailable).")
            return
        await record_action(
            self.bot,
            ctx.guild,
            "unwarn",
            target=member,
            moderator=ctx.author,
            reason=row.get("reason") or NO_REASON,
            metadata={"warning_id": warning_id},
            extra_fields=[("Warning ID", f"#{warning_id}")],
        )
        remaining = await self.bot.db.count_active_warnings(ctx.guild.id, member.id)
        await self._confirm(
            ctx,
            text=(
                f"Removed warning `#{warning_id}` from **{member}**. "
                f"Active warnings: {remaining}."
            ),
        )

    @commands.command(name="clear", aliases=["purge"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def clear(
        self,
        ctx: commands.Context,
        amount: int,
        member: discord.Member | None = None,
    ) -> None:
        """Delete recent messages (optionally only from one member)."""
        if amount < 1 or amount > MAX_CLEAR:
            await ctx.send(f"Amount must be between 1 and {MAX_CLEAR}.")
            return

        def check(message: discord.Message) -> bool:
            if message.pinned:
                return False
            return member is None or message.author.id == member.id

        try:
            deleted = await ctx.channel.purge(limit=amount, check=check)
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete messages here.")
            return
        except discord.HTTPException as exc:
            await ctx.send(f"Purge failed: {exc}")
            return
        scope = f" from **{member}**" if member else ""
        await record_action(
            self.bot,
            ctx.guild,
            "clear",
            target=member,
            moderator=ctx.author,
            reason=f"Deleted {len(deleted)} message(s){scope}",
            metadata={
                "channel_id": ctx.channel.id,
                "deleted": len(deleted),
                "requested": amount,
            },
            extra_fields=[("Channel", ctx.channel.mention)],
        )
        await ctx.send(
            f"Deleted {len(deleted)} message(s){scope}.",
            delete_after=5,
        )

    @commands.command(name="lock", aliases=["lockdown"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def lock(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | None = None,
        *,
        reason: str = NO_REASON,
    ) -> None:
        """Prevent @everyone from sending messages in a channel."""
        target = channel or ctx.channel
        overwrite = target.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        try:
            await target.set_permissions(
                ctx.guild.default_role,
                overwrite=overwrite,
                reason=_audit_reason(ctx, reason),
            )
        except discord.Forbidden:
            await ctx.send("I do not have permission to modify that channel.")
            return
        except discord.HTTPException as exc:
            await ctx.send(f"Lock failed: {exc}")
            return
        await record_action(
            self.bot,
            ctx.guild,
            "lock",
            moderator=ctx.author,
            reason=reason,
            metadata={"channel_id": target.id},
            extra_fields=[("Channel", target.mention)],
        )
        await self._confirm(
            ctx,
            text=f"Locked {target.mention}. Reason: {reason}",
            color=discord.Color.orange(),
        )

    @commands.command(name="unlock")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def unlock(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | None = None,
        *,
        reason: str = NO_REASON,
    ) -> None:
        """Remove the @everyone send-messages override in a channel."""
        target = channel or ctx.channel
        overwrite = target.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        try:
            await target.set_permissions(
                ctx.guild.default_role,
                overwrite=overwrite,
                reason=_audit_reason(ctx, reason),
            )
        except discord.Forbidden:
            await ctx.send("I do not have permission to modify that channel.")
            return
        except discord.HTTPException as exc:
            await ctx.send(f"Unlock failed: {exc}")
            return
        await record_action(
            self.bot,
            ctx.guild,
            "unlock",
            moderator=ctx.author,
            reason=reason,
            metadata={"channel_id": target.id},
            extra_fields=[("Channel", target.mention)],
        )
        await self._confirm(ctx, text=f"Unlocked {target.mention}. Reason: {reason}")

    @commands.command(name="modlog")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def modlog(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | str | None = None,
    ) -> None:
        """Set the moderation log channel (`!modlog #channel` or `!modlog off`)."""
        settings = await get_settings(self.bot, ctx.guild)
        if channel is None:
            current = settings.get("log_moderation_channel_id")
            await ctx.send(
                f"Moderation log channel: {f'<#{current}>' if current else 'not set'}"
            )
            return
        if isinstance(channel, str):
            if channel.lower() in {"off", "none", "disable"}:
                row = await save_settings(
                    self.bot, ctx.guild, {"log_moderation_channel_id": None}
                )
                await ctx.send(
                    "Moderation logging disabled."
                    if row
                    else "Could not update settings."
                )
                return
            try:
                channel = await commands.TextChannelConverter().convert(ctx, channel)
            except commands.BadArgument:
                await ctx.send("Provide a channel mention, ID, or `off`.")
                return
        row = await save_settings(
            self.bot, ctx.guild, {"log_moderation_channel_id": channel.id}
        )
        await ctx.send(
            f"Moderation logs will be posted in {channel.mention}."
            if row
            else "Could not update settings."
        )

    @commands.command(name="modlogs", aliases=["history"])
    @commands.guild_only()
    @mod_or_admin()
    async def modlogs(
        self,
        ctx: commands.Context,
        member: discord.User | None = None,
        limit: int = 10,
    ) -> None:
        """Show recent moderation history (optionally for one member)."""
        limit = max(1, min(limit, MAX_HISTORY))
        rows = await self.bot.db.list_moderation_logs(
            ctx.guild.id,
            target_id=member.id if member else None,
            limit=limit,
        )
        title = f"Moderation history for {member}" if member else "Moderation history"
        embed = discord.Embed(title=title, color=discord.Color.blurple())
        if not rows:
            embed.description = "No moderation actions recorded yet."
        else:
            for row in rows:
                moderator = row.get("moderator_id")
                target = row.get("target_id")
                lines = [row.get("reason") or NO_REASON]
                if moderator:
                    lines.append(f"Moderator: <@{moderator}>")
                if target and not member:
                    lines.append(f"Target: <@{target}>")
                embed.add_field(
                    name=(
                        f"{action_label(str(row.get('action')))} • "
                        f"{_format_ts(row.get('created_at'))}"
                    ),
                    value="\n".join(lines)[:1024],
                    inline=False,
                )
        embed.set_footer(text=f"Showing {len(rows)} of last {limit}")
        await ctx.send(embed=embed)


async def setup(bot) -> None:
    await bot.add_cog(Moderation(bot))
