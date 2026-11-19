from __future__ import annotations

import platform

import discord
from discord.ext import commands

from core.permissions import is_owner_or_guild_admin


class CoreAdmin(commands.Cog):
    """Core diagnostics and management commands for Phase 3 verification."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="botinfo")
    @is_owner_or_guild_admin()
    async def botinfo(self, ctx: commands.Context) -> None:
        """Show basic bot and runtime information."""
        user = self.bot.user
        app_name = getattr(user, "name", "Triumph Bot")
        guilds = len(getattr(self.bot, "guilds", []))
        latency_ms = getattr(self.bot, "latency", 0.0) * 1000
        prefix = ctx.prefix or getattr(self.bot.app_config, "bot_prefix", "!")

        embed = discord.Embed(title="Triumph Bot — Core Info", color=discord.Color.blurple())
        embed.add_field(name="Bot", value=f"{app_name}", inline=True)
        embed.add_field(name="Guilds", value=str(guilds), inline=True)
        embed.add_field(name="Latency", value=f"{latency_ms:.0f} ms", inline=True)
        embed.add_field(name="Prefix", value=f"`{prefix}`", inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)
        embed.add_field(
            name="DB configured",
            value=str(getattr(self.bot.db, "configured", False)),
            inline=True,
        )
        await ctx.send(embed=embed)

    @commands.command(name="dbping")
    @is_owner_or_guild_admin()
    async def dbping(self, ctx: commands.Context) -> None:
        """Check Supabase connectivity (service role)."""
        db = getattr(self.bot, "db", None)
        if db is None:
            await ctx.send("Database service is not initialized.")
            return
        ok, msg = await db.ping()
        status = "OK" if ok else "FAIL"
        await ctx.send(f"Supabase {status}: {msg}")

    @commands.command(name="extensions", aliases=["cogs"])
    @is_owner_or_guild_admin()
    async def extensions(self, ctx: commands.Context) -> None:
        """List loaded extensions/cogs."""
        exts = sorted(self.bot.extensions.keys())
        if not exts:
            await ctx.send("No extensions loaded.")
            return
        lines = "\n".join(f"- {e}" for e in exts)
        await ctx.send(f"Loaded extensions ({len(exts)}):\n{lines}")

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, extension: str) -> None:
        """Reload an extension (owner only). Usage: !reload cogs.general"""
        ext = extension if extension.startswith("cogs.") else f"cogs.{extension}"
        try:
            await self.bot.reload_extension(ext)
            await ctx.send(f"Reloaded `{ext}`.")
        except commands.ExtensionNotLoaded:
            try:
                await self.bot.load_extension(ext)
                await ctx.send(f"Loaded `{ext}` (was not loaded).")
            except Exception as exc:  # noqa: BLE001
                await ctx.send(f"Failed to load `{ext}`: {exc}")
        except Exception as exc:  # noqa: BLE001
            await ctx.send(f"Failed to reload `{ext}`: {exc}")

    @commands.command(name="prefix")
    @is_owner_or_guild_admin()
    async def show_prefix(self, ctx: commands.Context) -> None:
        """Show the effective prefix for this server/context."""
        await ctx.send(f"Current prefix: `{ctx.prefix}`")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CoreAdmin(bot))
