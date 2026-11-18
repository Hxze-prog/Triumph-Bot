from __future__ import annotations

import discord
from services.discord_links import emoji_key, parse_emoji, parse_message_link


def test_parse_guild_message_link():
    link = "https://discord.com/channels/123456789012345678/234567890123456789/345678901234567890"
    assert parse_message_link(link) == (
        123456789012345678,
        234567890123456789,
        345678901234567890,
    )


def test_parse_dm_message_link():
    link = "https://discordapp.com/channels/@me/234567890123456789/345678901234567890"
    assert parse_message_link(link) == (
        None,
        234567890123456789,
        345678901234567890,
    )


def test_parse_invalid_link():
    assert parse_message_link("") is None
    assert parse_message_link("not a link") is None
    assert parse_message_link("https://discord.com/channels/1/2") is None


def test_emoji_key():
    assert emoji_key(discord.PartialEmoji(name="👍")) == "👍"
    custom = discord.PartialEmoji(name="party", id=123456789012345678)
    assert emoji_key(custom) == "<:party:123456789012345678>"
    animated = discord.PartialEmoji(name="dance", id=123456789012345678, animated=True)
    assert emoji_key(animated) == "<a:dance:123456789012345678>"


def test_parse_emoji_accepts_unicode_and_custom():
    unicode_emoji = parse_emoji("👍")
    assert unicode_emoji is not None
    assert unicode_emoji.id is None
    assert emoji_key(unicode_emoji) == "👍"

    custom = parse_emoji("<:party:123456789012345678>")
    assert custom is not None
    assert custom.id == 123456789012345678
    assert custom.name == "party"

    animated = parse_emoji("<a:dance:123456789012345678>")
    assert animated is not None and animated.animated

    assert parse_emoji("") is None
    assert parse_emoji("   ") is None
