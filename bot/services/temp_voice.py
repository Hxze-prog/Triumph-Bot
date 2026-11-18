from __future__ import annotations

from services.templates import render

DEFAULT_TEMPLATE = "{user}'s Channel"
MAX_CHANNEL_NAME = 100


def build_channel_name(
    template: str | None,
    *,
    user: str,
    display_name: str,
    member_number: int | None = None,
) -> str:
    """Render the temp-voice name template, with safe fallbacks."""
    context = {
        "user": user,
        "name": user,
        "display_name": display_name,
        "mention": "",
        "member_number": str(member_number or 0),
        "server": "",
        "member_count": "0",
        "created_at": "",
        "joined_at": "",
        "account_age": "",
        "server_age": "",
    }
    rendered = render(template or DEFAULT_TEMPLATE, context).strip()
    if not rendered:
        rendered = f"{display_name or user}'s Channel"
    return rendered[:MAX_CHANNEL_NAME]


def normalize_limit(value: int | str | None) -> int:
    """Clamp a Discord voice user_limit into 0..99."""
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return max(0, min(99, number))
