from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

import discord
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands, tasks

from core.settings import get_settings
from core.settings_cache import TTLCache
from services.automations import (
    AUTOMATION_TYPES,
    CRON_HELP,
    automation_types,
    chunk_message,
    is_scheduled,
    render_message,
    response_matches,
    validate_cron,
)
from services.server_stats import collect_stats, stats_embed

logger = logging.getLogger(__name__)

MENTIONS = discord.AllowedMentions(everyone=False, roles=True, users=True)
MAX_NAME = 100
MAX_BODY = 4000


class Automations(commands.Cog, name="Automations"):
    """Database-backed automations and scheduled jobs."""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=UTC)
        self._response_cache = TTLCache(ttl_seconds=30.0)
        self._last_response: dict[int, float] = {}

    async def cog_load(self) -> None:
        self.scheduler.start()
        await self._load_jobs()
        self._refresh_jobs.start()

    async def cog_unload(self) -> None:
        self._refresh_jobs.cancel()
        try:
            self.scheduler.shutdown(wait=False)
        except Exception:
            logger.debug("Scheduler shutdown failed", exc_info=True)

    @tasks.loop(seconds=30)
    async def _refresh_jobs(self) -> None:
        try:
            await self._load_jobs(verbose=False)
        except Exception:
            logger.warning("Automation refresh failed", exc_info=True)

    @_refresh_jobs.before_loop
    async def _before_refresh_jobs(self) -> None:
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self._load_jobs(verbose=False)

    def _job_id(self, automation_id: int) -> str:
        return f"automation:{automation_id}"

    async def _load_jobs(self, *, verbose: bool = True) -> None:
        rows = await self.bot.db.list_automations(None, enabled_only=True)
        desired: set[str] = set()
        loaded = 0
        for row in rows:
            automation_id = int(row.get("id") or 0)
            if automation_id <= 0:
                continue
            if self._sync_job(row):
                desired.add(self._job_id(automation_id))
                loaded += 1

        for job in self.scheduler.get_jobs():
            if job.id.startswith("automation:") and job.id not in desired:
                try:
                    self.scheduler.remove_job(job.id)
                except JobLookupError:
                    pass

        if verbose:
            logger.info("Automation scheduler ready with %s job(s)", loaded)
        else:
            logger.debug("Automation scheduler synced with %s job(s)", loaded)

    def _sync_job(self, row: dict[str, Any]) -> bool:
        automation_id = int(row.get("id") or 0)
        if automation_id <= 0:
            return False
        job_id = self._job_id(automation_id)
        automation_type = str(row.get("type") or "")
        if not row.get("enabled") or not is_scheduled(automation_type):
            self._remove_job(automation_id)
            return False
        cron = row.get("cron")
        if not validate_cron(cron):
            logger.warning(
                "Automation %s has invalid cron %r; skipping", automation_id, cron
            )
            self._remove_job(automation_id)
            return False
        if self.scheduler.get_job(job_id) is not None:
            return True
        try:
            trigger = CronTrigger.from_crontab(str(cron).strip(), timezone=UTC)
        except (ValueError, TypeError) as exc:
            logger.warning("Could not build trigger for automation %s: %s", automation_id, exc)
            return False
        self.scheduler.add_job(
            self._run_job,
            trigger,
            args=[automation_id],
            id=job_id,
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=300,
        )
        return True

    def _remove_job(self, automation_id: int) -> None:
        try:
            self.scheduler.remove_job(self._job_id(automation_id))
        except JobLookupError:
            pass

    async def _run_job(self, automation_id: int) -> None:
        try:
            row = await self.bot.db.get_automation(automation_id)
            if not row or not row.get("enabled"):
                return
            guild = self.bot.get_guild(int(row.get("guild_id") or 0))
            if guild is None:
                return
            await self._dispatch(row, guild)
            await self.bot.db.mark_automation_run(
                automation_id, datetime.now(UTC).isoformat()
            )
        except Exception:
            logger.exception("Automation %s failed", automation_id)

    async def _dispatch(self, row: dict[str, Any], guild: discord.Guild) -> None:
        automation_type = str(row.get("type") or "")
        payload = row.get("payload") or {}
        channel_id = row.get("channel_id")
        channel = guild.get_channel(int(channel_id)) if channel_id else None

        if automation_type in {"announcement", "message", "reminder"}:
            if not isinstance(channel, discord.TextChannel):
                logger.warning(
                    "Automation %s channel is missing in guild %s",
                    row.get("id"),
                    guild.id,
                )
                return
            text = render_message(payload.get("message"), guild=guild)
            for chunk in chunk_message(text):
                await channel.send(chunk, allowed_mentions=MENTIONS)
            return

        if automation_type == "stats":
            stats = collect_stats(guild)
            await self.bot.db.add_server_stats(guild.id, stats)
            if isinstance(channel, discord.TextChannel):
                await channel.send(
                    embed=stats_embed(stats, title=f"Statistics: {guild.name}")
                )

    async def _send_hook(
        self,
        guild: discord.Guild,
        row: dict[str, Any],
        member: discord.Member,
    ) -> None:
        channel_id = row.get("channel_id")
        channel = guild.get_channel(int(channel_id)) if channel_id else None
        if not isinstance(channel, discord.TextChannel):
            return
        payload = row.get("payload") or {}
        text = render_message(payload.get("message"), guild=guild, member=member)
        for chunk in chunk_message(text):
            await channel.send(chunk, allowed_mentions=MENTIONS)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        guild = member.guild
        if guild is None:
            return
        hooks = await self.bot.db.list_automations(
            guild.id, automation_type="welcome", enabled_only=True
        )
        for row in hooks:
            await self._send_hook(guild, row, member)

        autoroles = await self.bot.db.list_automations(
            guild.id, automation_type="autorole", enabled_only=True
        )
        if not autoroles or guild.me is None:
            return
        assignable: list[discord.Role] = []
        for row in autoroles:
            payload = row.get("payload") or {}
            for role_id in payload.get("role_ids") or []:
                role = guild.get_role(int(role_id))
                if (
                    role is not None
                    and not role.is_default()
                    and not role.managed
                    and role < guild.me.top_role
                    and role not in assignable
                ):
                    assignable.append(role)
        if assignable:
            try:
                await member.add_roles(*assignable, reason="Automation autorole")
            except discord.HTTPException as exc:
                logger.warning(
                    "Automation autorole failed for %s in %s: %s",
                    member.id,
                    guild.id,
                    exc,
                )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        guild = member.guild
        if guild is None:
            return
        hooks = await self.bot.db.list_automations(
            guild.id, automation_type="goodbye", enabled_only=True
        )
        for row in hooks:
            await self._send_hook(guild, row, member)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot:
            return
        guild = message.guild
        rows = self._response_cache.get(guild.id)
        if rows is None:
            rows = await self.bot.db.list_automations(
                guild.id, automation_type="response", enabled_only=True
            )
            self._response_cache.set(guild.id, rows)
        if not rows:
            return
        content = message.content or ""
        for row in rows:
            payload = row.get("payload") or {}
            if not response_matches(payload, content):
                continue
            automation_id = int(row.get("id") or 0)
            now = time.monotonic()
            if now - self._last_response.get(automation_id, 0.0) < 3:
                continue
            self._last_response[automation_id] = now
            text = render_message(
                payload.get("response"), guild=guild, member=message.author
            )
            if not text:
                continue
            for chunk in chunk_message(text):
                await message.channel.send(chunk, allowed_mentions=MENTIONS)
            return

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    @commands.group(
        name="automation",
        aliases=["automations", "auto"],
        invoke_without_command=True,
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def automation(self, ctx: commands.Context) -> None:
        """Manage scheduled announcements, reminders, autoroles and responses."""
        await self._send_list(ctx)

    async def _send_list(self, ctx: commands.Context) -> None:
        rows = await self.bot.db.list_automations(ctx.guild.id)
        embed = discord.Embed(
            title="Automations",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        if not rows:
            embed.description = "No automations configured yet."
        else:
            lines = []
            for row in rows:
                state = "on" if row.get("enabled") else "off"
                line = (
                    f"`#{row.get('id')}` [{state}] **{row.get('type')}** "
                    f"{row.get('name')}"
                )
                if row.get("cron"):
                    line += f" | `{row.get('cron')}`"
                if row.get("channel_id"):
                    line += f" | <#{row.get('channel_id')}>"
                lines.append(line)
            embed.description = "\n".join(lines)[:4000]
        embed.set_footer(
            text="!automation remove|toggle <id|name> | Types: "
            + ", ".join(automation_types())
        )
        await ctx.send(embed=embed)

    @automation.command(name="list")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def list_cmd(self, ctx: commands.Context) -> None:
        """List automations for this server."""
        await self._send_list(ctx)

    @automation.command(name="status")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def status(self, ctx: commands.Context) -> None:
        """Show scheduler status and configuration help."""
        embed = discord.Embed(
            title="Automation scheduler",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name="Running",
            value="yes" if self.scheduler.running else "no",
            inline=True,
        )
        embed.add_field(
            name="Scheduled jobs",
            value=str(len(self.scheduler.get_jobs())),
            inline=True,
        )
        embed.add_field(
            name="Timezone",
            value="UTC",
            inline=True,
        )
        embed.add_field(
            name="Cron format",
            value=CRON_HELP,
            inline=False,
        )
        for key, meta in AUTOMATION_TYPES.items():
            embed.add_field(
                name=key,
                value=f"{meta['description']} ({'cron' if meta['scheduled'] else 'event hook'})",
                inline=False,
            )
        await ctx.send(embed=embed)

    def _validate_name(self, name: str) -> str | None:
        name = name.strip()
        if not name or len(name) > MAX_NAME:
            return None
        return name

    async def _store(
        self,
        ctx: commands.Context,
        automation_type: str,
        name: str,
        *,
        channel_id: int | None = None,
        cron: str | None = None,
        payload: dict[str, Any] | None = None,
        description: str = "",
    ) -> None:
        clean_name = self._validate_name(name)
        if clean_name is None:
            await ctx.send(f"Name must be 1-{MAX_NAME} characters.")
            return
        if cron is not None and not validate_cron(cron):
            await ctx.send(f"Invalid cron expression. Use {CRON_HELP}.")
            return
        await get_settings(self.bot, ctx.guild)
        row = await self.bot.db.add_automation(
            ctx.guild.id,
            automation_type,
            clean_name,
            channel_id=channel_id,
            cron=cron,
            payload=payload,
        )
        if row is None:
            await ctx.send("Could not save the automation (database unavailable).")
            return
        self._response_cache.invalidate(ctx.guild.id)
        self._sync_job(row)
        label = AUTOMATION_TYPES[automation_type]["label"]
        detail = f" `{cron}`" if cron else ""
        await ctx.send(
            f"Created {label} `#{row.get('id')}` **{clean_name}**{detail}"
            + (f" {description}" if description else "")
            + "."
        )

    @automation.command(name="announcement")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def announcement(
        self,
        ctx: commands.Context,
        name: str,
        cron: str,
        channel: discord.TextChannel,
        *,
        message: str,
    ) -> None:
        """Create a scheduled announcement: name, cron, channel, message."""
        message = message.strip()
        if not message or len(message) > MAX_BODY:
            await ctx.send(f"Message must be 1-{MAX_BODY} characters.")
            return
        await self._store(
            ctx,
            "announcement",
            name,
            channel_id=channel.id,
            cron=cron,
            payload={"message": message},
            description=f"in {channel.mention}",
        )

    @automation.command(name="message")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def message(
        self,
        ctx: commands.Context,
        name: str,
        cron: str,
        channel: discord.TextChannel,
        *,
        message: str,
    ) -> None:
        """Create a recurring automated message (same syntax as announcement)."""
        message = message.strip()
        if not message or len(message) > MAX_BODY:
            await ctx.send(f"Message must be 1-{MAX_BODY} characters.")
            return
        await self._store(
            ctx,
            "message",
            name,
            channel_id=channel.id,
            cron=cron,
            payload={"message": message},
            description=f"in {channel.mention}",
        )

    @automation.command(name="reminder")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def reminder(
        self,
        ctx: commands.Context,
        name: str,
        cron: str,
        channel: discord.TextChannel,
        *,
        message: str,
    ) -> None:
        """Create a recurring reminder (mentions in the message are allowed)."""
        message = message.strip()
        if not message or len(message) > MAX_BODY:
            await ctx.send(f"Message must be 1-{MAX_BODY} characters.")
            return
        await self._store(
            ctx,
            "reminder",
            name,
            channel_id=channel.id,
            cron=cron,
            payload={"message": message},
            description=f"in {channel.mention}",
        )

    @automation.command(name="stats")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def stats(
        self,
        ctx: commands.Context,
        name: str,
        cron: str,
        channel: discord.TextChannel | None = None,
    ) -> None:
        """Schedule periodic server statistics snapshots."""
        await self._store(
            ctx,
            "stats",
            name,
            channel_id=channel.id if channel else None,
            cron=cron,
            payload={},
            description=f"in {channel.mention}" if channel else "(stored only)",
        )

    @automation.command(name="autorole")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def autorole(
        self,
        ctx: commands.Context,
        name: str,
        roles: commands.Greedy[discord.Role],
    ) -> None:
        """Assign roles automatically when members join."""
        if not roles:
            await ctx.send("Provide at least one role.")
            return
        role_ids = [role.id for role in roles]
        await self._store(
            ctx,
            "autorole",
            name,
            payload={"role_ids": role_ids},
            description="Roles: " + " ".join(role.mention for role in roles),
        )

    @automation.command(name="welcome")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def welcome(
        self,
        ctx: commands.Context,
        name: str,
        channel: discord.TextChannel,
        *,
        message: str,
    ) -> None:
        """Send an extra welcome message on join."""
        message = message.strip()
        if not message or len(message) > MAX_BODY:
            await ctx.send(f"Message must be 1-{MAX_BODY} characters.")
            return
        await self._store(
            ctx,
            "welcome",
            name,
            channel_id=channel.id,
            payload={"message": message},
            description=f"in {channel.mention}",
        )

    @automation.command(name="goodbye")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def goodbye(
        self,
        ctx: commands.Context,
        name: str,
        channel: discord.TextChannel,
        *,
        message: str,
    ) -> None:
        """Send an extra goodbye message when a member leaves."""
        message = message.strip()
        if not message or len(message) > MAX_BODY:
            await ctx.send(f"Message must be 1-{MAX_BODY} characters.")
            return
        await self._store(
            ctx,
            "goodbye",
            name,
            channel_id=channel.id,
            payload={"message": message},
            description=f"in {channel.mention}",
        )

    @automation.command(name="response")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def response(
        self,
        ctx: commands.Context,
        name: str,
        trigger: str,
        *,
        message: str,
    ) -> None:
        """Reply automatically when a message contains a trigger phrase."""
        trigger = trigger.strip().lower()
        if not trigger or len(trigger) > 200:
            await ctx.send("Trigger must be 1-200 characters.")
            return
        message = message.strip()
        if not message or len(message) > MAX_BODY:
            await ctx.send(f"Response must be 1-{MAX_BODY} characters.")
            return
        await self._store(
            ctx,
            "response",
            name,
            payload={"trigger": trigger, "response": message},
            description=f"Trigger: `{trigger}`",
        )

    async def _resolve(
        self, ctx: commands.Context, value: str
    ) -> dict[str, Any] | None:
        rows = await self.bot.db.list_automations(ctx.guild.id)
        raw = value.strip().lstrip("#")
        if raw.isdigit():
            wanted = int(raw)
            for row in rows:
                if int(row.get("id") or 0) == wanted:
                    return row
            await ctx.send(f"No automation found with id #{wanted}.")
            return None
        matches = [
            row
            for row in rows
            if str(row.get("name") or "").lower() == value.strip().lower()
        ]
        if not matches:
            await ctx.send(f"No automation found named `{value}`.")
            return None
        if len(matches) > 1:
            await ctx.send(
                "Multiple automations share that name; use the numeric id instead."
            )
            return None
        return matches[0]

    @automation.command(name="remove")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def remove(self, ctx: commands.Context, automation: str) -> None:
        """Delete an automation by id or name."""
        row = await self._resolve(ctx, automation)
        if row is None:
            return
        automation_id = int(row.get("id") or 0)
        if not await self.bot.db.delete_automation(automation_id):
            await ctx.send("Could not delete the automation.")
            return
        self._remove_job(automation_id)
        self._response_cache.invalidate(ctx.guild.id)
        await ctx.send(
            f"Deleted automation `#{automation_id}` **{row.get('name')}**."
        )

    @automation.command(name="toggle")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def toggle(self, ctx: commands.Context, automation: str) -> None:
        """Enable or disable an automation by id or name."""
        row = await self._resolve(ctx, automation)
        if row is None:
            return
        automation_id = int(row.get("id") or 0)
        enabled = not bool(row.get("enabled"))
        updated = await self.bot.db.update_automation(
            automation_id, {"enabled": enabled}
        )
        if updated is None:
            await ctx.send("Could not update the automation.")
            return
        self._response_cache.invalidate(ctx.guild.id)
        self._sync_job(updated)
        await ctx.send(
            f"Automation `#{automation_id}` **{row.get('name')}** is now "
            + ("enabled." if enabled else "disabled.")
        )


async def setup(bot) -> None:
    await bot.add_cog(Automations(bot))
