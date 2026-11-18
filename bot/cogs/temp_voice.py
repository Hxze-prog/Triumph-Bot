from __future__ import annotations

import logging

import discord
from core.settings import get_settings, save_settings
from discord.ext import commands
from services.temp_voice import DEFAULT_TEMPLATE, build_channel_name, normalize_limit

logger = logging.getLogger(__name__)


class TempVoice(commands.Cog, name="TempVoice"):
    """Join-to-create temporary voice channels."""

    def __init__(self, bot) -> None:
        self.bot = bot
        self._reconciled = False

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if self._reconciled:
            return
        self._reconciled = True
        await self._reconcile()

    async def _reconcile(self) -> None:
        """Mark records whose channels no longer exist as deleted."""
        for guild in self.bot.guilds:
            rows = await self.bot.db.list_temp_voice_channels(guild.id)
            for row in rows:
                channel = guild.get_channel(int(row.get("channel_id") or 0))
                if not isinstance(channel, discord.VoiceChannel):
                    await self.bot.db.mark_temp_voice_deleted(
                        int(row["channel_id"]), discord.utils.utcnow().isoformat()
                    )
                    logger.info(
                        "Reconciled missing temp voice %s in guild %s",
                        row.get("channel_id"),
                        guild.id,
                    )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        record = await self.bot.db.get_temp_voice_channel(channel.id)
        if record and not record.get("deleted_at"):
            await self.bot.db.mark_temp_voice_deleted(
                channel.id, discord.utils.utcnow().isoformat()
            )

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        guild = member.guild
        if before.channel is not None and before.channel != after.channel:
            await self._delete_if_empty(before.channel, guild)

        if member.bot or after.channel is None:
            return
        settings = await get_settings(self.bot, guild)
        trigger_id = settings.get("temp_voice_trigger_channel_id")
        if not trigger_id or after.channel.id != int(trigger_id):
            return
        await self._create_for(member, settings)

    async def _delete_if_empty(
        self, channel: discord.abc.GuildChannel, guild: discord.Guild
    ) -> None:
        if not isinstance(channel, discord.VoiceChannel):
            return
        record = await self.bot.db.get_temp_voice_channel(channel.id)
        if record is None or record.get("deleted_at"):
            return
        if any(not member.bot for member in channel.members):
            return
        try:
            await channel.delete(reason="Temporary voice channel is empty")
        except discord.HTTPException as exc:
            logger.warning("Could not delete empty temp voice %s: %s", channel.id, exc)
            return
        await self.bot.db.mark_temp_voice_deleted(
            channel.id, discord.utils.utcnow().isoformat()
        )

    async def _create_for(self, member: discord.Member, settings: dict) -> None:
        guild = member.guild
        existing = await self._find_owned(guild, member.id)
        if existing is not None:
            if member.voice is None or member.voice.channel != existing:
                try:
                    await member.move_to(existing, reason="Return to own temporary channel")
                except discord.HTTPException as exc:
                    logger.warning("Could not move %s to temp voice: %s", member.id, exc)
            return

        category = None
        category_id = settings.get("temp_voice_category_id")
        if category_id:
            candidate = guild.get_channel(int(category_id))
            if isinstance(candidate, discord.CategoryChannel):
                category = candidate
        template = settings.get("temp_voice_name_template") or DEFAULT_TEMPLATE
        name = build_channel_name(
            template, user=member.name or str(member), display_name=member.display_name
        )
        limit = normalize_limit(settings.get("temp_voice_default_limit"))
        overwrites = {
            member: discord.PermissionOverwrite(
                manage_channels=True, move_members=True
            )
        }
        try:
            channel = await guild.create_voice_channel(
                name,
                category=category,
                user_limit=limit,
                overwrites=overwrites,
                reason=f"Temporary voice for {member} ({member.id})",
            )
        except discord.HTTPException as exc:
            logger.warning("Could not create temp voice for %s: %s", member.id, exc)
            return
        record = await self.bot.db.upsert_temp_voice_channel(
            channel.id,
            guild.id,
            member.id,
            channel_name=channel.name,
            user_limit=limit,
        )
        if record is None:
            try:
                await channel.delete(reason="Temporary voice record could not be saved")
            except discord.HTTPException:
                pass
            logger.warning(
                "Deleted untracked temp voice %s for %s (database unavailable)",
                channel.id,
                member.id,
            )
            return
        try:
            await member.move_to(channel, reason="Join-to-create temporary channel")
        except discord.HTTPException as exc:
            logger.warning("Could not move %s into new temp voice: %s", member.id, exc)

    async def _find_owned(
        self, guild: discord.Guild, owner_id: int
    ) -> discord.VoiceChannel | None:
        rows = await self.bot.db.list_temp_voice_channels(guild.id)
        for row in rows:
            if int(row.get("owner_id") or 0) != owner_id:
                continue
            channel = guild.get_channel(int(row.get("channel_id") or 0))
            if isinstance(channel, discord.VoiceChannel):
                return channel
        return None

    async def _owned(
        self, ctx: commands.Context
    ) -> tuple[discord.VoiceChannel, dict]:
        voice = getattr(ctx.author, "voice", None)
        channel = voice.channel if voice else None
        if not isinstance(channel, discord.VoiceChannel):
            raise commands.CheckFailure(
                "Join your temporary voice channel first."
            )
        record = await self.bot.db.get_temp_voice_channel(channel.id)
        if record is None or record.get("deleted_at"):
            raise commands.CheckFailure("This is not a tracked temporary channel.")
        if int(record.get("owner_id") or 0) != ctx.author.id:
            raise commands.CheckFailure("Only the channel owner can do that.")
        return channel, record

    @commands.group(name="tempvoice", aliases=["tv"], invoke_without_command=True)
    @commands.guild_only()
    async def tempvoice(self, ctx: commands.Context) -> None:
        """Temporary voice system settings and owner controls."""
        await self._send_status(ctx)

    async def _send_status(self, ctx: commands.Context) -> None:
        settings = await get_settings(self.bot, ctx.guild)
        rows = await self.bot.db.list_temp_voice_channels(ctx.guild.id)
        trigger = settings.get("temp_voice_trigger_channel_id")
        category = settings.get("temp_voice_category_id")
        embed = discord.Embed(title="Temporary voice channels", color=discord.Color.blurple())
        embed.add_field(
            name="Trigger channel",
            value=f"<#{trigger}>" if trigger else "not set",
            inline=True,
        )
        embed.add_field(
            name="Category",
            value=f"<#{category}>" if category else "none",
            inline=True,
        )
        embed.add_field(
            name="Default limit",
            value=str(settings.get("temp_voice_default_limit") or 0),
            inline=True,
        )
        embed.add_field(
            name="Name template",
            value=f"`{settings.get('temp_voice_name_template') or DEFAULT_TEMPLATE}`",
            inline=False,
        )
        embed.add_field(name="Active channels", value=str(len(rows)), inline=True)
        embed.set_footer(
            text="Setup: !tempvoice setup #trigger [#category] | Owner: name, size, lock, unlock, kick, claim, delete"
        )
        await ctx.send(embed=embed)

    @tempvoice.command(name="status")
    @commands.guild_only()
    async def status(self, ctx: commands.Context) -> None:
        """Show temp voice configuration."""
        await self._send_status(ctx)

    @tempvoice.command(name="setup")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def setup(
        self,
        ctx: commands.Context,
        trigger: discord.VoiceChannel,
        category: discord.CategoryChannel | None = None,
    ) -> None:
        """Set the join-to-create voice channel and optional category."""
        values: dict = {"temp_voice_trigger_channel_id": trigger.id}
        if category is not None:
            values["temp_voice_category_id"] = category.id
        row = await save_settings(self.bot, ctx.guild, values)
        if row is None:
            await ctx.send("Could not save settings (database unavailable).")
            return
        await ctx.send(
            f"Temporary voice trigger set to {trigger.mention}"
            + (f" in {category.name}." if category else ".")
        )

    @tempvoice.command(name="trigger")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def trigger_cmd(
        self, ctx: commands.Context, channel: discord.VoiceChannel
    ) -> None:
        """Change the join-to-create trigger channel."""
        row = await save_settings(
            self.bot, ctx.guild, {"temp_voice_trigger_channel_id": channel.id}
        )
        await ctx.send(
            f"Trigger channel set to {channel.mention}."
            if row
            else "Could not save settings."
        )

    @tempvoice.command(name="category")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def category_cmd(
        self, ctx: commands.Context, category: discord.CategoryChannel | str
    ) -> None:
        """Set the creation category (`none` for top-level)."""
        if isinstance(category, str):
            if category.lower() in {"none", "off"}:
                row = await save_settings(
                    self.bot, ctx.guild, {"temp_voice_category_id": None}
                )
                await ctx.send(
                    "Temp channels will be created without a category."
                    if row
                    else "Could not save settings."
                )
                return
            await ctx.send("Provide a category mention/name, or `none`.")
            return
        row = await save_settings(
            self.bot, ctx.guild, {"temp_voice_category_id": category.id}
        )
        await ctx.send(
            f"Temp channels will be created in **{category.name}**."
            if row
            else "Could not save settings."
        )

    @tempvoice.command(name="defaultlimit")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def defaultlimit(self, ctx: commands.Context, value: int) -> None:
        """Default member limit for new temp channels (0 = unlimited)."""
        limit = normalize_limit(value)
        row = await save_settings(
            self.bot, ctx.guild, {"temp_voice_default_limit": limit}
        )
        await ctx.send(
            f"Default temp voice limit set to **{limit}**."
            if row
            else "Could not save settings."
        )

    @tempvoice.command(name="template")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def template(self, ctx: commands.Context, *, template: str) -> None:
        """Set the name template (supports `{user}`, `{display_name}`)."""
        if len(template) > 100:
            await ctx.send("Template must be 100 characters or fewer.")
            return
        row = await save_settings(
            self.bot, ctx.guild, {"temp_voice_name_template": template}
        )
        await ctx.send(
            f"Temp voice template set to `{template}`."
            if row
            else "Could not save settings."
        )

    @tempvoice.command(name="name")
    @commands.guild_only()
    async def name(self, ctx: commands.Context, *, name: str) -> None:
        """Rename your temporary channel."""
        channel, _record = await self._owned(ctx)
        if not name.strip() or len(name) > 100:
            await ctx.send("Provide a name between 1 and 100 characters.")
            return
        try:
            await channel.edit(name=name.strip(), reason="Owner renamed temp channel")
        except discord.HTTPException as exc:
            await ctx.send(f"Could not rename the channel: {exc}")
            return
        await self.bot.db.update_temp_voice_channel(
            channel.id, {"channel_name": channel.name}
        )
        await ctx.send(f"Channel renamed to **{channel.name}**.")

    @tempvoice.command(name="size")
    @commands.guild_only()
    async def size(self, ctx: commands.Context, value: int) -> None:
        """Change your temporary channel's member limit (0 = unlimited)."""
        channel, _record = await self._owned(ctx)
        limit = normalize_limit(value)
        try:
            await channel.edit(
                user_limit=limit, reason="Owner changed temp channel limit"
            )
        except discord.HTTPException as exc:
            await ctx.send(f"Could not change the limit: {exc}")
            return
        await self.bot.db.update_temp_voice_channel(channel.id, {"user_limit": limit})
        await ctx.send(
            f"Member limit set to **{limit}**."
            if limit
            else "Member limit removed (unlimited)."
        )

    @tempvoice.command(name="lock")
    @commands.guild_only()
    async def lock(self, ctx: commands.Context) -> None:
        """Prevent new members from joining your temporary channel."""
        channel, _record = await self._owned(ctx)
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.connect = False
        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite=overwrite,
                reason="Owner locked temp channel",
            )
        except discord.HTTPException as exc:
            await ctx.send(f"Could not lock the channel: {exc}")
            return
        await self.bot.db.update_temp_voice_channel(channel.id, {"is_locked": True})
        await ctx.send(f"Locked {channel.mention}.")

    @tempvoice.command(name="unlock")
    @commands.guild_only()
    async def unlock(self, ctx: commands.Context) -> None:
        """Allow members to join your temporary channel again."""
        channel, _record = await self._owned(ctx)
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.connect = None
        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite=overwrite,
                reason="Owner unlocked temp channel",
            )
        except discord.HTTPException as exc:
            await ctx.send(f"Could not unlock the channel: {exc}")
            return
        await self.bot.db.update_temp_voice_channel(channel.id, {"is_locked": False})
        await ctx.send(f"Unlocked {channel.mention}.")

    @tempvoice.command(name="kick")
    @commands.guild_only()
    async def kick(self, ctx: commands.Context, member: discord.Member) -> None:
        """Disconnect a member from your temporary channel."""
        channel, _record = await self._owned(ctx)
        if member.id == ctx.author.id:
            await ctx.send("You cannot kick yourself.")
            return
        if member not in channel.members:
            await ctx.send("That member is not in your channel.")
            return
        try:
            await member.move_to(None, reason=f"Kicked from temp channel by {ctx.author}")
        except discord.HTTPException as exc:
            await ctx.send(f"Could not disconnect that member: {exc}")
            return
        await ctx.send(f"Disconnected **{member}** from {channel.mention}.")

    @tempvoice.command(name="claim")
    @commands.guild_only()
    async def claim(self, ctx: commands.Context) -> None:
        """Claim ownership when the previous owner has left the channel."""
        voice = getattr(ctx.author, "voice", None)
        channel = voice.channel if voice else None
        if not isinstance(channel, discord.VoiceChannel):
            await ctx.send("Join the temporary channel first.")
            return
        record = await self.bot.db.get_temp_voice_channel(channel.id)
        if record is None or record.get("deleted_at"):
            await ctx.send("This is not a tracked temporary channel.")
            return
        if int(record.get("owner_id") or 0) == ctx.author.id:
            await ctx.send("You already own this channel.")
            return
        owner = channel.guild.get_member(int(record.get("owner_id") or 0))
        if owner is not None and owner in channel.members:
            await ctx.send("The owner is still in the channel.")
            return
        if owner is not None:
            try:
                await channel.set_permissions(owner, overwrite=None)
            except discord.HTTPException:
                pass
        try:
            await channel.set_permissions(
                ctx.author,
                overwrite=discord.PermissionOverwrite(
                    manage_channels=True, move_members=True
                ),
                reason="Temp channel ownership claimed",
            )
        except discord.HTTPException as exc:
            await ctx.send(f"Could not claim the channel: {exc}")
            return
        await self.bot.db.update_temp_voice_channel(
            channel.id, {"owner_id": ctx.author.id}
        )
        await ctx.send(f"You now own {channel.mention}.")

    @tempvoice.command(name="delete")
    @commands.guild_only()
    async def delete(self, ctx: commands.Context) -> None:
        """Delete your temporary channel."""
        channel, _record = await self._owned(ctx)
        try:
            await channel.delete(reason=f"Owner deleted temp channel ({ctx.author})")
        except discord.HTTPException as exc:
            await ctx.send(f"Could not delete the channel: {exc}")
            return
        await self.bot.db.mark_temp_voice_deleted(
            channel.id, discord.utils.utcnow().isoformat()
        )
        await ctx.send("Temporary channel deleted.", delete_after=5)


async def setup(bot) -> None:
    await bot.add_cog(TempVoice(bot))
