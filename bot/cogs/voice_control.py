from __future__ import annotations

import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class VoiceControl(commands.Cog, name="VoiceControl"):
    """Join and leave voice channels on demand."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _permission_problem(
        self, channel: discord.VoiceChannel, member: discord.Member
    ) -> str | None:
        permissions = channel.permissions_for(member)
        missing: list[str] = []
        if not permissions.view_channel:
            missing.append("View Channel")
        if not permissions.connect:
            missing.append("Connect")
        if not missing:
            return None
        return f"I need these permissions in {channel.mention}: {', '.join(missing)}."

    @commands.command(name="join")
    @commands.guild_only()
    @commands.has_guild_permissions(move_members=True)
    async def join(
        self,
        ctx: commands.Context,
        channel: discord.VoiceChannel | None = None,
    ) -> None:
        """Join a voice channel by ID or mention."""
        if ctx.guild is None or ctx.guild.me is None:
            await ctx.send("I cannot resolve my server permissions.")
            return

        if channel is None:
            author_voice = getattr(ctx.author, "voice", None)
            channel = author_voice.channel if author_voice else None
        if not isinstance(channel, discord.VoiceChannel):
            await ctx.send(
                "Usage: `!join <voice_channel>` or join a voice channel first."
            )
            return

        problem = self._permission_problem(channel, ctx.guild.me)
        if problem is not None:
            await ctx.send(problem)
            return

        voice = ctx.voice_client
        if voice is not None and voice.is_connected():
            if voice.channel == channel:
                await ctx.send(f"I am already in {channel.mention}.")
                return
            try:
                await voice.move_to(channel)
            except (discord.ClientException, discord.HTTPException) as exc:
                logger.exception("Could not move to voice channel %s", channel.id)
                await ctx.send(f"Could not move to {channel.mention}: {exc}")
                return
            await ctx.send(f"Moved to {channel.mention}.")
            return

        if voice is not None:
            try:
                await voice.disconnect(force=True)
            except Exception:
                logger.exception("Could not clear stale voice client")

        try:
            await channel.connect(timeout=30, reconnect=True, self_deaf=True)
        except RuntimeError:
            logger.exception("Voice dependencies are missing")
            await ctx.send(
                "Voice support is not installed on the bot host. "
                'Redeploy after installing `discord.py[voice]`.'
            )
            return
        except TimeoutError:
            logger.exception("Timed out joining voice channel %s", channel.id)
            await ctx.send(f"Timed out joining {channel.mention}.")
            return
        except (discord.ClientException, discord.HTTPException) as exc:
            logger.exception("Could not join voice channel %s", channel.id)
            await ctx.send(f"Could not join {channel.mention}: {exc}")
            return

        await ctx.send(f"Joined {channel.mention}.")

    @commands.command(name="leave")
    @commands.guild_only()
    @commands.has_guild_permissions(move_members=True)
    async def leave(self, ctx: commands.Context) -> None:
        """Disconnect from the current voice channel."""
        voice = ctx.voice_client
        if voice is None:
            await ctx.send("I am not in a voice channel.")
            return
        try:
            await voice.disconnect(force=True)
        except (discord.ClientException, discord.HTTPException) as exc:
            logger.exception("Could not leave voice channel")
            await ctx.send(f"Could not leave the voice channel: {exc}")
            return
        await ctx.send("Disconnected from the voice channel.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceControl(bot))
