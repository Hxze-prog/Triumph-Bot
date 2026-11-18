from __future__ import annotations

import logging

import discord
from core.settings import get_settings
from discord.ext import commands
from services.discord_links import emoji_key, parse_emoji, parse_message_link

logger = logging.getLogger(__name__)


def _message_link(guild_id: int, channel_id: int, message_id: int) -> str:
    return f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"


class ReactionRoles(commands.Cog, name="ReactionRoles"):
    """Self-assignable roles through message reactions."""

    def __init__(self, bot) -> None:
        self.bot = bot

    async def _resolve_message(
        self, ctx: commands.Context, target: str
    ) -> discord.Message:
        link = parse_message_link(target)
        if link is not None:
            guild_id, channel_id, message_id = link
            if guild_id is not None and guild_id != ctx.guild.id:
                raise commands.BadArgument("The message link must be from this server.")
            channel = ctx.guild.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await ctx.guild.fetch_channel(channel_id)
                except discord.HTTPException as exc:
                    raise commands.BadArgument(f"Could not load that channel: {exc}")
        else:
            try:
                message_id = int(target)
            except ValueError:
                raise commands.BadArgument(
                    "Provide a message ID or a Discord message link."
                )
            channel = ctx.channel
        if not isinstance(channel, discord.TextChannel):
            raise commands.BadArgument("Reaction roles need a text channel message.")
        try:
            return await channel.fetch_message(message_id)
        except discord.NotFound:
            raise commands.BadArgument("Message not found in that channel.")
        except discord.HTTPException as exc:
            raise commands.BadArgument(f"Could not load that message: {exc}")

    @commands.group(name="reactionrole", aliases=["rr"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole(self, ctx: commands.Context) -> None:
        """Manage reaction roles. Use `!reactionrole list` to see mappings."""
        await self._list(ctx)

    @reactionrole.command(name="add")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def add(
        self,
        ctx: commands.Context,
        target: str,
        emoji: str,
        role: discord.Role,
    ) -> None:
        """Map an emoji on a message to a role: `!reactionrole add <msg_id|link> <emoji> @role`."""
        parsed = parse_emoji(emoji)
        if parsed is None:
            await ctx.send("Provide a unicode emoji or `<:name:id>` custom emoji.")
            return
        if role.is_default():
            await ctx.send("The @everyone role cannot be used.")
            return
        if role.managed:
            await ctx.send("That role is managed by an integration and cannot be assigned.")
            return
        me = ctx.guild.me
        if me is None or role >= me.top_role:
            await ctx.send("That role is not below my highest role; move my role higher.")
            return
        await get_settings(self.bot, ctx.guild)
        message = await self._resolve_message(ctx, target)
        key = emoji_key(parsed)
        existing = await self.bot.db.get_reaction_role(message.id, key)
        if existing is not None:
            await ctx.send("That emoji is already mapped on this message.")
            return
        try:
            await message.add_reaction(parsed)
        except discord.HTTPException as exc:
            await ctx.send(f"Could not add that reaction: {exc}")
            return
        row = await self.bot.db.add_reaction_role(
            ctx.guild.id, message.id, message.channel.id, key, role.id
        )
        if row is None:
            try:
                await message.remove_reaction(parsed, ctx.guild.me)
            except discord.HTTPException:
                pass
            await ctx.send("Could not save the mapping (database unavailable).")
            return
        embed = discord.Embed(
            title="Reaction role added",
            description=(
                f"{key} on [message]({message.jump_url}) gives {role.mention}\n"
                f"Message ID: `{message.id}`"
            ),
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @reactionrole.command(name="remove")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def remove(
        self,
        ctx: commands.Context,
        target: str,
        emoji: str,
    ) -> None:
        """Remove a mapping: `!reactionrole remove <msg_id|link> <emoji>`."""
        parsed = parse_emoji(emoji)
        if parsed is None:
            await ctx.send("Provide a unicode emoji or `<:name:id>` custom emoji.")
            return
        message = await self._resolve_message(ctx, target)
        key = emoji_key(parsed)
        removed = await self.bot.db.remove_reaction_role(ctx.guild.id, message.id, key)
        if not removed:
            await ctx.send("No mapping found for that message and emoji.")
            return
        try:
            await message.remove_reaction(parsed, ctx.guild.me)
        except discord.HTTPException:
            pass
        await ctx.send(f"Removed reaction role {key} from message `{message.id}`.")

    @reactionrole.command(name="list")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def list_(self, ctx: commands.Context) -> None:
        """List reaction-role mappings in this server."""
        await self._list(ctx)

    async def _list(self, ctx: commands.Context) -> None:
        rows = await self.bot.db.list_reaction_roles(ctx.guild.id)
        embed = discord.Embed(title="Reaction roles", color=discord.Color.blurple())
        if not rows:
            embed.description = (
                "No mappings yet. Add one with "
                "`!reactionrole add <message_id|link> <emoji> @role`."
            )
            await ctx.send(embed=embed)
            return
        for row in rows[:25]:
            role_id = int(row.get("role_id") or 0)
            role = ctx.guild.get_role(role_id)
            role_text = role.mention if role else f"deleted role `{role_id}`"
            message_link = _message_link(
                ctx.guild.id, int(row.get("channel_id") or 0), int(row.get("message_id") or 0)
            )
            embed.add_field(
                name=f"{row.get('emoji')} -> {role_text}",
                value=f"[message]({message_link}) • `{row.get('message_id')}`",
                inline=False,
            )
        if len(rows) > 25:
            embed.set_footer(text=f"Showing 25 of {len(rows)} mappings")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self._handle(payload, add=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        await self._handle(payload, add=False)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        removed = await self.bot.db.delete_reaction_roles_for_message(payload.message_id)
        if removed:
            logger.info(
                "Removed %s reaction-role mapping(s) for deleted message %s",
                removed,
                payload.message_id,
            )

    async def _handle(
        self, payload: discord.RawReactionActionEvent, *, add: bool
    ) -> None:
        if payload.guild_id is None:
            return
        if self.bot.user is not None and payload.user_id == self.bot.user.id:
            return
        key = str(payload.emoji)
        mapping = await self.bot.db.get_reaction_role(payload.message_id, key)
        if mapping is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        role = guild.get_role(int(mapping.get("role_id") or 0))
        if role is None:
            return
        member = payload.member or guild.get_member(payload.user_id)
        if member is None:
            try:
                member = await guild.fetch_member(payload.user_id)
            except discord.HTTPException:
                return
        if member.bot:
            return
        me = guild.me
        if me is None or role >= me.top_role or role.managed or role.is_default():
            logger.warning(
                "Cannot assign reaction role %s in guild %s (hierarchy/managed)",
                role.id,
                guild.id,
            )
            return
        try:
            if add:
                await member.add_roles(role, reason=f"Reaction role ({key})")
            else:
                await member.remove_roles(role, reason=f"Reaction role removed ({key})")
        except discord.HTTPException as exc:
            logger.warning(
                "Reaction role update failed for %s/%s: %s", member.id, role.id, exc
            )


async def setup(bot) -> None:
    await bot.add_cog(ReactionRoles(bot))
