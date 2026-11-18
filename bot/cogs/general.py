from __future__ import annotations

import time

from discord.ext import commands


class General(commands.Cog):
    """Basic commands for connectivity and diagnostics."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        """Check bot responsiveness and latency."""
        start = time.perf_counter()
        message = await ctx.send("Pinging...")
        elapsed_ms = (time.perf_counter() - start) * 1000
        ws_ms = self.bot.latency * 1000
        await message.edit(
            content=f"Pong! WS: {ws_ms:.0f}ms | RTT: {elapsed_ms:.0f}ms"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
