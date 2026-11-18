from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from cogs.welcome import Welcome


def make_member() -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=1,
        name="alice",
        display_name="Alice",
        mention="<@1>",
        guild=SimpleNamespace(name="Triumph HQ", icon=None),
        created_at=now - timedelta(days=30),
        joined_at=now,
        display_avatar=None,
    )


def test_welcome_payload_embed_color_is_int() -> None:
    cog = Welcome(bot=SimpleNamespace())
    payload = asyncio.run(cog._welcome_payload(make_member(), {}, 3))

    embed = payload["embed"]
    assert isinstance(embed.color.value, int)
    assert embed.image.url == "attachment://welcome-1.png"
    assert payload["file"].filename == "welcome-1.png"
