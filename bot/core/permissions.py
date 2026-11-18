from __future__ import annotations

import discord
from discord.ext import commands


def guild_only():
    """Ensure command is used in a guild context."""
    return commands.guild_only()


def is_bot_owner():
    """Restrict command to the bot/application owner."""
    return commands.is_owner()


def is_guild_admin():
    """Restrict to guild members with Administrator permission."""

    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None or not isinstance(ctx.author, discord.Member):
            raise commands.NoPrivateMessage("This command can only be used in a server.")
        if ctx.author.guild_permissions.administrator:
            return True
        raise commands.MissingPermissions(["administrator"])

    return commands.check(predicate)


def can_manage_guild():
    """Restrict to members who can manage the guild or are administrators."""

    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None or not isinstance(ctx.author, discord.Member):
            raise commands.NoPrivateMessage("This command can only be used in a server.")
        perms = ctx.author.guild_permissions
        if perms.administrator or perms.manage_guild:
            return True
        raise commands.MissingPermissions(["manage_guild"])

    return commands.check(predicate)


def mod_or_admin():
    """Restrict to members with common moderation or admin permissions."""

    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None or not isinstance(ctx.author, discord.Member):
            raise commands.NoPrivateMessage("This command can only be used in a server.")
        perms = ctx.author.guild_permissions
        if (
            perms.administrator
            or perms.manage_guild
            or perms.manage_messages
            or perms.kick_members
            or perms.ban_members
            or perms.moderate_members
        ):
            return True
        raise commands.MissingPermissions(["moderation"])

    return commands.check(predicate)


def is_owner_or_guild_admin():
    """Allow bot owner or guild administrator."""

    async def predicate(ctx: commands.Context) -> bool:
        try:
            is_owner = await ctx.bot.is_owner(ctx.author)
        except Exception:  # noqa: BLE001 - owner lookup may fail before app info is ready
            is_owner = False
        if is_owner:
            return True
        if ctx.guild is None or not isinstance(ctx.author, discord.Member):
            raise commands.CheckFailure("This command requires bot owner or server admin.")
        if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
            return True
        raise commands.CheckFailure("This command requires bot owner or server admin.")

    return commands.check(predicate)
