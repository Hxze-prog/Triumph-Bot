from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from io import BytesIO
from typing import Any, TypeVar

import discord
from core.permissions import can_manage_guild
from discord.ext import commands
from services import banner as banner_service
from services import templates

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

MAX_MESSAGE_LENGTH = 1900


def admin_command(func: F) -> F:
    func = commands.guild_only()(func)
    func = can_manage_guild()(func)
    return func


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in {"on", "true", "yes", "enable", "enabled", "1"}:
        return True
    if lowered in {"off", "false", "no", "disable", "disabled", "0"}:
        return False
    return None


def _clip(text: str) -> str:
    return text if len(text) <= MAX_MESSAGE_LENGTH else text[: MAX_MESSAGE_LENGTH - 3] + "..."


class Welcome(commands.Cog):
    """Welcome, goodbye, autorole and member record management (Phase 4)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------ helpers

    async def _settings(self, guild: discord.Guild) -> dict[str, Any]:
        cached = self.bot.settings_cache.get(guild.id)
        if isinstance(cached, dict):
            return cached
        row = await self.bot.db.get_guild_settings(guild.id)
        settings = row if isinstance(row, dict) else {}
        self.bot.settings_cache.set(guild.id, settings)
        return settings

    async def _save(self, guild: discord.Guild, **values: Any) -> dict[str, Any] | None:
        await self.bot.db.upsert_guild(
            guild.id,
            name=guild.name,
            icon_url=str(guild.icon.url) if guild.icon else None,
            owner_id=guild.owner_id,
        )
        row = await self.bot.db.upsert_guild_settings(guild.id, values)
        if row is not None:
            self.bot.settings_cache.set(guild.id, row)
        return row

    async def _asset_bytes(self, asset: discord.Asset | None, size: int) -> bytes | None:
        if asset is None:
            return None
        try:
            return await asset.replace(size=size).read()
        except Exception as exc:  # noqa: BLE001 - CDN failures must not break events
            logger.debug("Failed to fetch asset %s: %s", asset, exc)
            return None

    async def _resolve_channel(self, guild: discord.Guild, channel_id: Any) -> discord.TextChannel | None:
        if not channel_id:
            return None
        try:
            channel = guild.get_channel(int(channel_id))
            if channel is None:
                channel = await guild.fetch_channel(int(channel_id))
        except (ValueError, TypeError, discord.HTTPException):
            return None
        return channel if isinstance(channel, discord.TextChannel) else None

    async def _assign_auto_roles(self, member: discord.Member, settings: dict[str, Any]) -> None:
        role_ids = settings.get("auto_role_ids") or []
        if not role_ids:
            return
        me = member.guild.me
        if me is None:
            return
        for raw_id in role_ids:
            try:
                role_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            role = member.guild.get_role(role_id)
            if role is None or role.is_default():
                continue
            if not me.guild_permissions.manage_roles:
                logger.warning(
                    "Cannot assign auto roles in guild %s: missing Manage Roles permission",
                    member.guild.id,
                )
                return
            if role >= me.top_role:
                logger.warning(
                    "Skipping auto role %s in guild %s: role is not below the bot's top role",
                    role.id,
                    member.guild.id,
                )
                continue
            try:
                await member.add_roles(role, reason="Autorole (welcome)")
            except discord.HTTPException as exc:
                logger.warning("Failed to assign auto role %s to %s: %s", role.id, member.id, exc)

    async def _welcome_payload(
        self,
        member: discord.Member,
        settings: dict[str, Any],
        member_number: int | None,
    ) -> dict[str, Any]:
        context = templates.member_context(member, member_number=member_number)
        message_text = templates.render(
            settings.get("welcome_message") or templates.DEFAULT_WELCOME_MESSAGE, context
        )
        embed_enabled = bool(settings.get("welcome_embed_enabled", True))
        banner_enabled = bool(settings.get("welcome_banner_enabled", True))

        icon_bytes = await self._asset_bytes(member.guild.icon, 64)
        accent = banner_service.accent_from_image(icon_bytes)

        file: discord.File | None = None
        if banner_enabled:
            avatar_bytes = await self._asset_bytes(member.display_avatar, 256)
            subtitle = templates.render(
                settings.get("welcome_banner_template") or templates.DEFAULT_BANNER_TEMPLATE,
                context,
            )
            number_text = str(member_number) if member_number is not None else "?"
            footer = f"Member #{number_text} | Joined {context['joined_at']}"
            try:
                png = await asyncio.to_thread(
                    banner_service.render_banner,
                    display_name=member.display_name,
                    subtitle=subtitle,
                    footer=footer,
                    server_name=member.guild.name,
                    avatar_bytes=avatar_bytes,
                    accent=accent,
                    initial=member.display_name[:1],
                )
                file = discord.File(
                    BytesIO(png),
                    filename=banner_service.banner_filename(member.id),
                )
            except Exception:
                logger.exception("Failed to render welcome banner for %s", member.id)
                file = None

        payload: dict[str, Any] = {}
        if embed_enabled:
            embed = discord.Embed(
                description=_clip(message_text),
                color=discord.Color.from_rgb(*accent),
            )
            avatar_url = getattr(member.display_avatar, "url", None)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            if file is not None:
                embed.set_image(url=f"attachment://{file.filename}")
            payload["embed"] = embed
        else:
            payload["content"] = _clip(message_text)
        if file is not None:
            payload["file"] = file
        return payload

    async def _send_welcome(
        self,
        member: discord.Member,
        settings: dict[str, Any],
        member_number: int | None,
    ) -> None:
        if not settings.get("welcome_enabled"):
            return
        channel = await self._resolve_channel(member.guild, settings.get("welcome_channel_id"))
        if channel is None:
            logger.info(
                "Welcome enabled for guild %s but no valid welcome channel is configured",
                member.guild.id,
            )
            return
        payload = await self._welcome_payload(member, settings, member_number)
        try:
            await channel.send(**payload)
        except discord.HTTPException as exc:
            logger.warning("Failed to send welcome message in guild %s: %s", member.guild.id, exc)

    async def _send_welcome_dm(
        self,
        member: discord.Member,
        settings: dict[str, Any],
        member_number: int | None,
    ) -> None:
        if not settings.get("welcome_dm_enabled"):
            return
        context = templates.member_context(member, member_number=member_number)
        text = templates.render(
            settings.get("welcome_dm_message") or templates.DEFAULT_WELCOME_MESSAGE, context
        )
        try:
            await member.send(_clip(text))
        except discord.Forbidden:
            logger.debug("Welcome DM blocked by user %s", member.id)
        except discord.HTTPException as exc:
            logger.warning("Failed to send welcome DM to %s: %s", member.id, exc)

    # ------------------------------------------------------------------- events

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return
        guild = member.guild
        try:
            await self.bot.db.upsert_guild(
                guild.id,
                name=guild.name,
                icon_url=str(guild.icon.url) if guild.icon else None,
                owner_id=guild.owner_id,
            )
            settings = await self._settings(guild)

            existing = await self.bot.db.get_member(guild.id, member.id)
            member_number = existing.get("member_number") if existing else None
            if member_number is None:
                member_number = await self.bot.db.next_member_number(guild.id)

            await self.bot.db.upsert_member(
                guild.id,
                member.id,
                {
                    "member_number": member_number,
                    "username": member.name,
                    "display_name": member.display_name,
                    "avatar_url": getattr(member.display_avatar, "url", None),
                    "account_created_at": member.created_at.isoformat(),
                    "joined_at": (member.joined_at or datetime.now(UTC)).isoformat(),
                    "left_at": None,
                    "is_bot": member.bot,
                },
            )

            await self._assign_auto_roles(member, settings)
            await self._send_welcome(member, settings, member_number)
            await self._send_welcome_dm(member, settings, member_number)
        except Exception:
            logger.exception("Welcome flow failed for member %s in guild %s", member.id, guild.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        if member.bot:
            return
        guild = member.guild
        try:
            record = await self.bot.db.get_member(guild.id, member.id)
            await self.bot.db.set_member_left(guild.id, member.id, _now_iso())

            settings = await self._settings(guild)
            if not settings.get("goodbye_enabled"):
                return
            channel = await self._resolve_channel(guild, settings.get("goodbye_channel_id"))
            if channel is None:
                return

            member_number = record.get("member_number") if record else None
            context = templates.member_context(member, member_number=member_number)
            text = templates.render(
                settings.get("goodbye_message") or templates.DEFAULT_GOODBYE_MESSAGE, context
            )
            try:
                await channel.send(_clip(text))
            except discord.HTTPException as exc:
                logger.warning("Failed to send goodbye message in guild %s: %s", guild.id, exc)
        except Exception:
            logger.exception("Goodbye flow failed for member %s in guild %s", member.id, guild.id)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if after.bot:
            return
        if (
            before.name == after.name
            and before.display_name == after.display_name
            and before.display_avatar == after.display_avatar
        ):
            return
        await self.bot.db.update_member(
            after.guild.id,
            after.id,
            {
                "username": after.name,
                "display_name": after.display_name,
                "avatar_url": getattr(after.display_avatar, "url", None),
            },
        )

    # ----------------------------------------------------------------- commands

    @commands.group(name="welcome", invoke_without_command=True)
    @admin_command
    async def welcome(self, ctx: commands.Context) -> None:
        """Show welcome settings."""
        settings = await self._settings(ctx.guild)
        channel = await self._resolve_channel(ctx.guild, settings.get("welcome_channel_id"))
        roles = settings.get("auto_role_ids") or []
        lines = [
            f"Welcome: {'on' if settings.get('welcome_enabled') else 'off'}",
            f"Channel: {channel.mention if channel else 'not set'}",
            f"Embed: {'on' if settings.get('welcome_embed_enabled', True) else 'off'}",
            f"Banner: {'on' if settings.get('welcome_banner_enabled', True) else 'off'}",
            f"DM: {'on' if settings.get('welcome_dm_enabled') else 'off'}",
            f"Autoroles: {len(roles)}",
            f"Message: {settings.get('welcome_message') or templates.DEFAULT_WELCOME_MESSAGE}",
            f"Banner template: {settings.get('welcome_banner_template') or templates.DEFAULT_BANNER_TEMPLATE}",
        ]
        await ctx.send("\n".join(lines))

    @welcome.command(name="channel")
    @admin_command
    async def welcome_channel(self, ctx: commands.Context, channel: str | None = None) -> None:
        """Set the welcome channel (`!welcome channel #channel` or `off`)."""
        if channel is None:
            settings = await self._settings(ctx.guild)
            current = await self._resolve_channel(ctx.guild, settings.get("welcome_channel_id"))
            await ctx.send(f"Welcome channel: {current.mention if current else 'not set'}")
            return
        if channel.strip().lower() in {"off", "none", "clear"}:
            await self._save(ctx.guild, welcome_channel_id=None)
            await ctx.send("Welcome channel cleared.")
            return
        converter = commands.TextChannelConverter()
        try:
            text_channel = await converter.convert(ctx, channel)
        except commands.BadArgument:
            await ctx.send("Unknown channel. Mention a channel or use its ID.")
            return
        await self._save(ctx.guild, welcome_channel_id=text_channel.id)
        await ctx.send(f"Welcome channel set to {text_channel.mention}.")

    @welcome.command(name="message")
    @admin_command
    async def welcome_message(self, ctx: commands.Context, *, message: str | None = None) -> None:
        """Set the welcome message (supports {user}, {server}, {member_number}, ...)."""
        if message is None:
            settings = await self._settings(ctx.guild)
            await ctx.send(
                f"Current message: {settings.get('welcome_message') or templates.DEFAULT_WELCOME_MESSAGE}"
            )
            return
        await self._save(ctx.guild, welcome_message=message.strip())
        await ctx.send("Welcome message updated.")

    @welcome.command(name="template")
    @admin_command
    async def welcome_template(self, ctx: commands.Context, *, template: str | None = None) -> None:
        """Set the banner subtitle template."""
        if template is None:
            settings = await self._settings(ctx.guild)
            await ctx.send(
                "Current banner template: "
                f"{settings.get('welcome_banner_template') or templates.DEFAULT_BANNER_TEMPLATE}"
            )
            return
        await self._save(ctx.guild, welcome_banner_template=template.strip())
        await ctx.send("Welcome banner template updated.")

    @welcome.command(name="toggle")
    @admin_command
    async def welcome_toggle(self, ctx: commands.Context) -> None:
        """Enable or disable welcome messages."""
        settings = await self._settings(ctx.guild)
        enabled = not bool(settings.get("welcome_enabled"))
        await self._save(ctx.guild, welcome_enabled=enabled)
        await ctx.send(f"Welcome messages {'enabled' if enabled else 'disabled'}.")

    @welcome.command(name="embed")
    @admin_command
    async def welcome_embed(self, ctx: commands.Context, state: str | None = None) -> None:
        """Turn welcome embeds on/off (`!welcome embed on|off`)."""
        settings = await self._settings(ctx.guild)
        value = _parse_bool(state)
        if state is not None and value is None:
            await ctx.send("Use `on` or `off`.")
            return
        enabled = (not bool(settings.get("welcome_embed_enabled", True))) if value is None else value
        await self._save(ctx.guild, welcome_embed_enabled=enabled)
        await ctx.send(f"Welcome embeds {'enabled' if enabled else 'disabled'}.")

    @welcome.command(name="banner")
    @admin_command
    async def welcome_banner(self, ctx: commands.Context, state: str | None = None) -> None:
        """Turn welcome banners on/off (`!welcome banner on|off`)."""
        settings = await self._settings(ctx.guild)
        value = _parse_bool(state)
        if state is not None and value is None:
            await ctx.send("Use `on` or `off`.")
            return
        enabled = (not bool(settings.get("welcome_banner_enabled", True))) if value is None else value
        await self._save(ctx.guild, welcome_banner_enabled=enabled)
        await ctx.send(f"Welcome banners {'enabled' if enabled else 'disabled'}.")

    @welcome.command(name="dm")
    @admin_command
    async def welcome_dm(self, ctx: commands.Context, state: str | None = None) -> None:
        """Turn welcome DMs on/off (`!welcome dm on|off`)."""
        settings = await self._settings(ctx.guild)
        value = _parse_bool(state)
        if state is not None and value is None:
            await ctx.send("Use `on` or `off`.")
            return
        enabled = (not bool(settings.get("welcome_dm_enabled"))) if value is None else value
        await self._save(ctx.guild, welcome_dm_enabled=enabled)
        await ctx.send(f"Welcome DMs {'enabled' if enabled else 'disabled'}.")

    @welcome.command(name="test")
    @admin_command
    async def welcome_test(
        self,
        ctx: commands.Context,
        target: discord.Member | discord.TextChannel | None = None,
    ) -> None:
        """Preview the welcome output in the configured channel (or `#channel`/`@member`)."""
        member = target if isinstance(target, discord.Member) else ctx.author
        settings = await self._settings(ctx.guild)
        channel: discord.TextChannel | None = (
            target if isinstance(target, discord.TextChannel) else None
        )
        if channel is None:
            channel = await self._resolve_channel(
                ctx.guild, settings.get("welcome_channel_id")
            )
        if channel is None:
            channel = ctx.channel
        record = await self.bot.db.get_member(ctx.guild.id, member.id)
        member_number = record.get("member_number") if record else None
        payload = await self._welcome_payload(member, settings, member_number)
        try:
            await channel.send(**payload)
        except discord.HTTPException as exc:
            await ctx.send(f"Could not send preview to {channel.mention}: {exc}")
            return
        if channel.id != getattr(ctx.channel, "id", None):
            await ctx.send(f"Preview sent to {channel.mention}.", delete_after=10)

    @commands.group(name="goodbye", invoke_without_command=True)
    @admin_command
    async def goodbye(self, ctx: commands.Context) -> None:
        """Show goodbye settings."""
        settings = await self._settings(ctx.guild)
        channel = await self._resolve_channel(ctx.guild, settings.get("goodbye_channel_id"))
        lines = [
            f"Goodbye: {'on' if settings.get('goodbye_enabled') else 'off'}",
            f"Channel: {channel.mention if channel else 'not set'}",
            f"Message: {settings.get('goodbye_message') or templates.DEFAULT_GOODBYE_MESSAGE}",
        ]
        await ctx.send("\n".join(lines))

    @goodbye.command(name="channel")
    @admin_command
    async def goodbye_channel(self, ctx: commands.Context, channel: str | None = None) -> None:
        """Set the goodbye channel (`!goodbye channel #channel` or `off`)."""
        if channel is None:
            settings = await self._settings(ctx.guild)
            current = await self._resolve_channel(ctx.guild, settings.get("goodbye_channel_id"))
            await ctx.send(f"Goodbye channel: {current.mention if current else 'not set'}")
            return
        if channel.strip().lower() in {"off", "none", "clear"}:
            await self._save(ctx.guild, goodbye_channel_id=None)
            await ctx.send("Goodbye channel cleared.")
            return
        converter = commands.TextChannelConverter()
        try:
            text_channel = await converter.convert(ctx, channel)
        except commands.BadArgument:
            await ctx.send("Unknown channel. Mention a channel or use its ID.")
            return
        await self._save(ctx.guild, goodbye_channel_id=text_channel.id)
        await ctx.send(f"Goodbye channel set to {text_channel.mention}.")

    @goodbye.command(name="message")
    @admin_command
    async def goodbye_message(self, ctx: commands.Context, *, message: str | None = None) -> None:
        """Set the goodbye message."""
        if message is None:
            settings = await self._settings(ctx.guild)
            await ctx.send(
                f"Current message: {settings.get('goodbye_message') or templates.DEFAULT_GOODBYE_MESSAGE}"
            )
            return
        await self._save(ctx.guild, goodbye_message=message.strip())
        await ctx.send("Goodbye message updated.")

    @goodbye.command(name="toggle")
    @admin_command
    async def goodbye_toggle(self, ctx: commands.Context) -> None:
        """Enable or disable goodbye messages."""
        settings = await self._settings(ctx.guild)
        enabled = not bool(settings.get("goodbye_enabled"))
        await self._save(ctx.guild, goodbye_enabled=enabled)
        await ctx.send(f"Goodbye messages {'enabled' if enabled else 'disabled'}.")

    @goodbye.command(name="test")
    @admin_command
    async def goodbye_test(
        self,
        ctx: commands.Context,
        target: discord.Member | discord.TextChannel | None = None,
    ) -> None:
        """Preview the goodbye message in the configured channel (or `#channel`/`@member`)."""
        member = target if isinstance(target, discord.Member) else ctx.author
        settings = await self._settings(ctx.guild)
        channel: discord.TextChannel | None = (
            target if isinstance(target, discord.TextChannel) else None
        )
        if channel is None:
            channel = await self._resolve_channel(
                ctx.guild, settings.get("goodbye_channel_id")
            )
        if channel is None:
            channel = ctx.channel
        record = await self.bot.db.get_member(ctx.guild.id, member.id)
        member_number = record.get("member_number") if record else None
        context = templates.member_context(member, member_number=member_number)
        text = templates.render(
            settings.get("goodbye_message") or templates.DEFAULT_GOODBYE_MESSAGE, context
        )
        try:
            await channel.send(_clip(text))
        except discord.HTTPException as exc:
            await ctx.send(f"Could not send preview to {channel.mention}: {exc}")
            return
        if channel.id != getattr(ctx.channel, "id", None):
            await ctx.send(f"Preview sent to {channel.mention}.", delete_after=10)

    @commands.group(name="autorole", invoke_without_command=True)
    @admin_command
    async def autorole(self, ctx: commands.Context) -> None:
        """Show auto roles assigned on join."""
        await self._send_autorole_list(ctx)

    async def _send_autorole_list(self, ctx: commands.Context) -> None:
        settings = await self._settings(ctx.guild)
        roles = []
        for role_id in settings.get("auto_role_ids") or []:
            role = ctx.guild.get_role(int(role_id))
            roles.append(role.mention if role else f"`{role_id}` (missing)")
        await ctx.send("Autoroles: " + (", ".join(roles) if roles else "none"))

    @autorole.command(name="add")
    @admin_command
    async def autorole_add(self, ctx: commands.Context, role: discord.Role) -> None:
        """Add a role to the autorole list."""
        if role.is_default():
            await ctx.send("The @everyone role cannot be an autorole.")
            return
        me = ctx.guild.me
        if me is not None and role >= me.top_role:
            await ctx.send("That role is above my top role, so I cannot assign it.")
            return
        settings = await self._settings(ctx.guild)
        current = [int(value) for value in settings.get("auto_role_ids") or []]
        if role.id in current:
            await ctx.send(f"{role.mention} is already an autorole.")
            return
        current.append(role.id)
        await self._save(ctx.guild, auto_role_ids=current)
        await ctx.send(f"Added {role.mention} to autoroles.")

    @autorole.command(name="remove")
    @admin_command
    async def autorole_remove(self, ctx: commands.Context, role: discord.Role) -> None:
        """Remove a role from the autorole list."""
        settings = await self._settings(ctx.guild)
        current = [int(value) for value in settings.get("auto_role_ids") or []]
        if role.id not in current:
            await ctx.send(f"{role.mention} is not an autorole.")
            return
        current = [value for value in current if value != role.id]
        await self._save(ctx.guild, auto_role_ids=current)
        await ctx.send(f"Removed {role.mention} from autoroles.")

    @autorole.command(name="list")
    @admin_command
    async def autorole_list(self, ctx: commands.Context) -> None:
        """List configured autoroles."""
        await self._send_autorole_list(ctx)

    @autorole.command(name="clear")
    @admin_command
    async def autorole_clear(self, ctx: commands.Context) -> None:
        """Remove all autoroles."""
        await self._save(ctx.guild, auto_role_ids=[])
        await ctx.send("Autoroles cleared.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Welcome(bot))
