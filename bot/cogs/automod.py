from __future__ import annotations

import logging
import time
from datetime import timedelta

import discord
from discord.ext import commands

from core.permissions import can_manage_guild
from core.settings import get_settings, save_settings
from services.automod_rules import (
    ALLOWED_DOMAINS,
    SpamTracker,
    contains_invite,
    find_disallowed_links,
)
from services.durations import MAX_TIMEOUT, format_seconds, parse_duration
from services.modlog import record_action

logger = logging.getLogger(__name__)

TOGGLE_KEYS = {
    "spam": "automod_anti_spam_enabled",
    "links": "automod_anti_link_enabled",
    "invites": "automod_anti_invite_enabled",
}

TRUE_WORDS = {"on", "true", "yes", "enable", "enabled", "1"}
FALSE_WORDS = {"off", "false", "no", "disable", "disabled", "0"}

PRUNE_EVERY_SECONDS = 300.0


def _is_exempt(member: discord.Member, guild: discord.Guild) -> bool:
    if member.id == guild.owner_id:
        return True
    perms = member.guild_permissions
    return bool(
        perms.administrator
        or perms.manage_messages
        or perms.manage_guild
        or perms.kick_members
        or perms.ban_members
        or perms.moderate_members
    )


class AutoMod(commands.Cog, name="AutoMod"):
    """Deletes spam and disallowed links/invites, with database-backed config."""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.tracker = SpamTracker()
        self._last_prune = time.monotonic()

    def _prune(self) -> None:
        now = time.monotonic()
        if now - self._last_prune < PRUNE_EVERY_SECONDS:
            return
        self.tracker.prune(now=now, interval=PRUNE_EVERY_SECONDS)
        self._last_prune = now

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot:
            return
        member = message.author
        if not isinstance(member, discord.Member):
            return
        if _is_exempt(member, message.guild):
            return

        settings = await get_settings(self.bot, message.guild)
        spam_on = bool(settings.get(TOGGLE_KEYS["spam"]))
        link_on = bool(settings.get(TOGGLE_KEYS["links"]))
        invite_on = bool(settings.get(TOGGLE_KEYS["invites"]))
        if not (spam_on or link_on or invite_on):
            return

        content = message.content or ""
        if invite_on and contains_invite(content):
            await self._delete(message)
            await record_action(
                self.bot,
                message.guild,
                "automod_invite",
                target=member,
                moderator=message.guild.me,
                reason="Posted a Discord invite link",
                metadata={
                    "channel_id": message.channel.id,
                    "content": content[:500],
                },
                extra_fields=[("Channel", message.channel.mention)],
            )
            return

        if link_on:
            links = find_disallowed_links(content)
            if links:
                await self._delete(message)
                await record_action(
                    self.bot,
                    message.guild,
                    "automod_link",
                    target=member,
                    moderator=message.guild.me,
                    reason="Posted a disallowed link",
                    metadata={
                        "channel_id": message.channel.id,
                        "content": content[:500],
                        "links": links[:5],
                    },
                    extra_fields=[("Channel", message.channel.mention)],
                )
                return

        if spam_on:
            self._prune()
            threshold = int(settings.get("automod_spam_threshold") or 5)
            interval = float(settings.get("automod_spam_interval_seconds") or 5)
            key = (message.guild.id, member.id)
            triggered = self.tracker.hit(
                key,
                now=time.monotonic(),
                threshold=threshold,
                interval=interval,
            )
            if triggered:
                self.tracker.reset(key)
                await self._handle_spam(
                    message, member, settings, threshold, interval
                )

    @staticmethod
    async def _delete(message: discord.Message) -> None:
        try:
            await message.delete()
        except discord.HTTPException:
            pass

    async def _handle_spam(
        self,
        message: discord.Message,
        member: discord.Member,
        settings: dict,
        threshold: int,
        interval: float,
    ) -> None:
        now = discord.utils.utcnow()
        try:
            await message.channel.purge(
                limit=100,
                check=lambda m: (
                    not m.pinned
                    and m.author.id == member.id
                    and (now - m.created_at).total_seconds() <= interval + 2
                ),
            )
        except discord.HTTPException:
            await self._delete(message)

        timeout_seconds = int(settings.get("automod_timeout_seconds") or 0)
        timeout_applied = False
        if timeout_seconds > 0:
            duration = min(timedelta(seconds=timeout_seconds), MAX_TIMEOUT)
            try:
                await member.timeout(
                    duration,
                    reason=(
                        f"Automod: {threshold}+ messages within "
                        f"{format_seconds(interval)}"
                    ),
                )
                timeout_applied = True
            except discord.HTTPException:
                timeout_applied = False

        await record_action(
            self.bot,
            message.guild,
            "automod_spam",
            target=member,
            moderator=message.guild.me,
            reason=(
                f"Sent {threshold}+ messages within {format_seconds(interval)}"
            ),
            metadata={
                "channel_id": message.channel.id,
                "threshold": threshold,
                "interval_seconds": interval,
                "timeout_seconds": timeout_seconds if timeout_applied else 0,
            },
            extra_fields=[
                ("Channel", message.channel.mention),
                (
                    "Timeout",
                    format_seconds(timeout_seconds) if timeout_applied else "none",
                ),
            ],
        )

    def _status_embed(self, settings: dict) -> discord.Embed:
        embed = discord.Embed(
            title="Automod settings",
            color=discord.Color.blurple(),
        )
        for label, key in (
            ("Anti-spam", TOGGLE_KEYS["spam"]),
            ("Anti-link", TOGGLE_KEYS["links"]),
            ("Anti-invite", TOGGLE_KEYS["invites"]),
        ):
            embed.add_field(
                name=label,
                value="enabled" if settings.get(key) else "disabled",
                inline=True,
            )
        embed.add_field(
            name="Spam rule",
            value=(
                f"{settings.get('automod_spam_threshold') or 5} messages / "
                f"{format_seconds(settings.get('automod_spam_interval_seconds') or 5)}"
            ),
            inline=True,
        )
        embed.add_field(
            name="Spam timeout",
            value=format_seconds(settings.get("automod_timeout_seconds") or 0),
            inline=True,
        )
        log_channel = settings.get("log_moderation_channel_id")
        embed.add_field(
            name="Mod log channel",
            value=f"<#{log_channel}>" if log_channel else "not set",
            inline=True,
        )
        embed.add_field(
            name="Link allowlist",
            value=", ".join(sorted(ALLOWED_DOMAINS))[:1024],
            inline=False,
        )
        return embed

    @commands.group(name="automod", invoke_without_command=True)
    @commands.guild_only()
    @can_manage_guild()
    async def automod(self, ctx: commands.Context) -> None:
        """Show or change automod settings."""
        settings = await get_settings(self.bot, ctx.guild)
        await ctx.send(embed=self._status_embed(settings))

    async def _set_toggle(self, ctx: commands.Context, feature: str, state: str) -> None:
        value = state.strip().lower()
        if value in TRUE_WORDS:
            enabled = True
        elif value in FALSE_WORDS:
            enabled = False
        else:
            await ctx.send("Use `on` or `off`.")
            return
        row = await save_settings(self.bot, ctx.guild, {TOGGLE_KEYS[feature]: enabled})
        if row is None:
            await ctx.send("Could not update settings (database unavailable).")
            return
        await ctx.send(f"Automod {feature}: **{'enabled' if enabled else 'disabled'}**.")

    @automod.command(name="spam")
    @commands.guild_only()
    @can_manage_guild()
    async def automod_spam(self, ctx: commands.Context, state: str) -> None:
        """Enable/disable anti-spam (`!automod spam on|off`)."""
        await self._set_toggle(ctx, "spam", state)

    @automod.command(name="links")
    @commands.guild_only()
    @can_manage_guild()
    async def automod_links(self, ctx: commands.Context, state: str) -> None:
        """Enable/disable anti-link (`!automod links on|off`)."""
        await self._set_toggle(ctx, "links", state)

    @automod.command(name="invites")
    @commands.guild_only()
    @can_manage_guild()
    async def automod_invites(self, ctx: commands.Context, state: str) -> None:
        """Enable/disable anti-invite (`!automod invites on|off`)."""
        await self._set_toggle(ctx, "invites", state)

    @automod.command(name="threshold")
    @commands.guild_only()
    @can_manage_guild()
    async def automod_threshold(self, ctx: commands.Context, value: int) -> None:
        """Messages needed before spam triggers (1-50)."""
        if value < 1 or value > 50:
            await ctx.send("Threshold must be between 1 and 50.")
            return
        row = await save_settings(
            self.bot, ctx.guild, {"automod_spam_threshold": value}
        )
        await ctx.send(
            f"Spam threshold set to **{value}** message(s)."
            if row
            else "Could not update settings."
        )

    @automod.command(name="interval")
    @commands.guild_only()
    @can_manage_guild()
    async def automod_interval(self, ctx: commands.Context, seconds: str) -> None:
        """Spam window length (`!automod interval 5s` or seconds)."""
        value = int(seconds) if seconds.isdigit() else None
        if value is None:
            delta = parse_duration(seconds)
            if delta is not None:
                value = int(delta.total_seconds())
        if value is None or value < 1 or value > 3600:
            await ctx.send("Interval must be between 1 second and 1 hour.")
            return
        row = await save_settings(
            self.bot, ctx.guild, {"automod_spam_interval_seconds": value}
        )
        await ctx.send(
            f"Spam interval set to **{format_seconds(value)}**."
            if row
            else "Could not update settings."
        )

    @automod.command(name="timeout")
    @commands.guild_only()
    @can_manage_guild()
    async def automod_timeout(self, ctx: commands.Context, value: str) -> None:
        """Timeout applied to spammers (`!automod timeout 10m`, `off`)."""
        if value.strip().lower() in FALSE_WORDS | {"none"}:
            row = await save_settings(
                self.bot, ctx.guild, {"automod_timeout_seconds": 0}
            )
            await ctx.send(
                "Spam timeout disabled." if row else "Could not update settings."
            )
            return
        delta = parse_duration(value)
        if delta is None:
            await ctx.send("Use a duration like `10m`, `1h`, or `off`.")
            return
        seconds = int(delta.total_seconds())
        row = await save_settings(
            self.bot, ctx.guild, {"automod_timeout_seconds": seconds}
        )
        await ctx.send(
            f"Spam timeout set to **{format_seconds(seconds)}**."
            if row
            else "Could not update settings."
        )

    @automod.command(name="status")
    @commands.guild_only()
    @can_manage_guild()
    async def automod_status(self, ctx: commands.Context) -> None:
        """Show current automod settings."""
        settings = await get_settings(self.bot, ctx.guild)
        await ctx.send(embed=self._status_embed(settings))


async def setup(bot) -> None:
    await bot.add_cog(AutoMod(bot))
