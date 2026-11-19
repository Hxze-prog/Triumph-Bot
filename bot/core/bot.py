from __future__ import annotations

import logging
from pathlib import Path

import discord
from discord.ext import commands

from config import Config
from core.database import Database
from core.settings_cache import TTLCache

logger = logging.getLogger(__name__)


class TriumphBot(commands.Bot):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True  # Server Members Intent (must be enabled in portal)
        intents.message_content = True  # Message Content Intent (required for ! prefix)
        intents.voice_states = True
        intents.moderation = True
        # intents.presences = True  # Privileged; enable later if needed for stats

        super().__init__(
            command_prefix=self._get_prefix,
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=False),
        )
        self.app_config = config
        self.db = Database(config.supabase_url, config.supabase_service_role_key)
        self.settings_cache = TTLCache(ttl_seconds=30.0)

    async def _get_prefix(self, _bot: commands.Bot, message: discord.Message):
        default = self.app_config.bot_prefix or "!"
        guild = message.guild
        if guild is None:
            return commands.when_mentioned_or(default)(self, message)

        cached = self.settings_cache.get(guild.id)
        prefix = None
        if isinstance(cached, dict):
            prefix = cached.get("prefix")
        elif cached is None:
            settings = await self.db.get_guild_settings(guild.id)
            if isinstance(settings, dict):
                self.settings_cache.set(guild.id, settings)
                prefix = settings.get("prefix")
            else:
                # Cache miss/negative briefly to avoid hammering DB when unavailable.
                self.settings_cache.set(guild.id, {}, ttl=15.0)

        if not isinstance(prefix, str) or not prefix.strip():
            prefix = default
        return commands.when_mentioned_or(prefix)(self, message)

    async def setup_hook(self) -> None:
        # Load all cogs in bot/cogs except __init__.
        cogs_dir = Path(__file__).resolve().parent.parent / "cogs"
        for path in sorted(cogs_dir.glob("*.py")):
            if path.name.startswith("_") or path.name == "__init__.py":
                continue
            ext = f"cogs.{path.stem}"
            try:
                await self.load_extension(ext)
                logger.info("Loaded extension: %s", ext)
            except Exception:
                logger.exception("Failed to load extension: %s", ext)

    async def on_connect(self) -> None:
        logger.info("Connected to Discord gateway.")

    async def on_disconnect(self) -> None:
        logger.warning("Disconnected from Discord gateway. Reconnect will be attempted automatically.")

    async def on_resumed(self) -> None:
        logger.info("Discord session resumed.")

    async def on_ready(self) -> None:
        assert self.user is not None
        logger.info("Logged in as %s (id=%s)", self.user, self.user.id)
        logger.info("Guilds: %s", len(self.guilds))
        _ok, msg = await self.db.ping()
        logger.info("Supabase: %s", msg)

    async def on_error(self, event_method: str, /, *args, **kwargs) -> None:
        logger.exception("Unhandled exception in event: %s", event_method)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        # Unwrap CommandInvokeError to handle the original cause cleanly.
        original = error
        if isinstance(error, commands.CommandInvokeError) and error.original is not None:
            original = error.original

        if isinstance(original, commands.CommandNotFound):
            return
        if isinstance(original, commands.NotOwner):
            await ctx.send("This command is restricted to the bot owner.")
            return
        if isinstance(original, commands.NoPrivateMessage):
            await ctx.send("This command can only be used in a server.")
            return
        if isinstance(original, commands.MissingPermissions):
            perms = ", ".join(getattr(original, "missing_permissions", [])) or "required permissions"
            await ctx.send(f"You do not have permission to use this command ({perms}).")
            return
        if isinstance(original, commands.BotMissingPermissions):
            perms = ", ".join(getattr(original, "missing_permissions", [])) or "required permissions"
            await ctx.send(f"I am missing required permissions to do that ({perms}).")
            return
        if isinstance(original, commands.MissingRequiredArgument):
            param = getattr(original, "param", None)
            name = getattr(param, "name", "argument")
            cmd = ctx.command.qualified_name if ctx.command else "command"
            await ctx.send(f"Missing argument: `{name}`. Use `{ctx.prefix}help {cmd}`.")
            return
        if isinstance(original, commands.BadArgument):
            await ctx.send(f"Invalid argument: {original}")
            return
        if isinstance(original, commands.TooManyArguments):
            await ctx.send("Too many arguments provided.")
            return
        if isinstance(original, commands.CommandOnCooldown):
            await ctx.send(f"Command on cooldown. Try again in {original.retry_after:.1f}s.")
            return
        if isinstance(original, commands.CheckFailure):
            # Generic check failure (custom checks should raise with messages where possible).
            msg = str(original)
            if msg and msg != "The check functions for command failed.":
                await ctx.send(msg)
            else:
                await ctx.send("You do not meet the requirements to use this command.")
            return
        if isinstance(original, commands.DisabledCommand):
            await ctx.send("This command is currently disabled.")
            return
        if isinstance(original, commands.MaxConcurrencyReached):
            await ctx.send("This command is already running. Please wait and try again.")
            return

        # Unexpected errors: log with context, respond generically.
        guild_id = ctx.guild.id if ctx.guild else None
        channel_id = ctx.channel.id if ctx.channel else None
        logger.exception(
            "Unhandled command error (cmd=%s guild=%s channel=%s user=%s): %s",
            getattr(ctx.command, "qualified_name", None),
            guild_id,
            channel_id,
            getattr(ctx.author, "id", None),
            original,
        )
        try:
            await ctx.send("An unexpected error occurred. Please try again later.")
        except Exception:
            logger.exception("Failed to send command error response.")
