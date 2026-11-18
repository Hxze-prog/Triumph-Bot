from __future__ import annotations

import discord

NUMBER_EMOJIS = (
    "\u0031\ufe0f\u20e3",
    "\u0032\ufe0f\u20e3",
    "\u0033\ufe0f\u20e3",
    "\u0034\ufe0f\u20e3",
    "\u0035\ufe0f\u20e3",
    "\u0036\ufe0f\u20e3",
    "\u0037\ufe0f\u20e3",
    "\u0038\ufe0f\u20e3",
    "\u0039\ufe0f\u20e3",
    "\U0001f51f",
)

MAX_OPTIONS = len(NUMBER_EMOJIS)
MAX_QUESTION = 256
MAX_OPTION = 80


def normalize_emoji(value: str) -> str:
    """Drop variation selectors so keycap emojis compare consistently."""
    return str(value).replace("\ufe0f", "")


def option_emoji(index: int) -> str:
    return NUMBER_EMOJIS[index] if index < len(NUMBER_EMOJIS) else ""


def parse_poll_body(body: str) -> tuple[str, list[str]]:
    """Parse `Question | Option 1 | Option 2` into question + options.

    Raises ValueError with a user-facing message on invalid input.
    """
    parts = [part.strip() for part in (body or "").split("|")]
    if len(parts) < 3:
        raise ValueError("Use `!poll Question | Option 1 | Option 2` (2-10 options).")
    question = parts[0]
    options = [part for part in parts[1:] if part]
    if not question:
        raise ValueError("The poll needs a question.")
    if len(question) > MAX_QUESTION:
        raise ValueError(f"Question must be {MAX_QUESTION} characters or fewer.")
    if len(options) < 2:
        raise ValueError("Provide at least two options.")
    if len(options) > MAX_OPTIONS:
        raise ValueError(f"Provide at most {MAX_OPTIONS} options.")
    for option in options:
        if len(option) > MAX_OPTION:
            raise ValueError(f"Options must be {MAX_OPTION} characters or fewer.")
    return question, options


def poll_embed(question: str, options: list[str], author: str | None = None) -> discord.Embed:
    embed = discord.Embed(title=question[:MAX_QUESTION], color=discord.Color.blurple())
    lines = [
        f"{NUMBER_EMOJIS[index]} {option}"
        for index, option in enumerate(options[:MAX_OPTIONS])
    ]
    embed.description = "\n".join(lines)
    if author:
        embed.set_footer(text=f"Poll by {author}")
    return embed
