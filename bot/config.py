from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BOT_DIR = Path(__file__).resolve().parent
ROOT_DIR = BOT_DIR.parent


def _load_env() -> None:
    # Prefer bot-local .env, then fall back to root .env for convenience.
    load_dotenv(BOT_DIR / ".env")
    load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Config:
    discord_token: str | None
    discord_guild_id: int | None
    supabase_url: str | None
    supabase_service_role_key: str | None
    bot_prefix: str
    log_level: str
    host: str
    port: int

    @property
    def discord_ready(self) -> bool:
        return bool(self.discord_token and self.discord_token != "your_discord_bot_token_here")

    @property
    def supabase_ready(self) -> bool:
        return bool(
            self.supabase_url
            and self.supabase_service_role_key
            and self.supabase_url != "https://your-project-ref.supabase.co"
            and self.supabase_service_role_key != "your_supabase_service_role_key_here"
        )


def _get_int(name: str) -> int | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def load_config() -> Config:
    _load_env()
    return Config(
        discord_token=os.getenv("DISCORD_TOKEN"),
        discord_guild_id=_get_int("DISCORD_GUILD_ID"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        bot_prefix=os.getenv("BOT_PREFIX", "!"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )
