from __future__ import annotations

import logging

from config import load_config
from core.bot import TriumphBot
from core.health import start_health_server
from core.logging import setup_logging

logger = logging.getLogger(__name__)


def main() -> int:
    config = load_config()
    setup_logging(config.log_level)

    logger.info("Triumph Bot starting")
    logger.info("Discord configured: %s", config.discord_ready)
    logger.info("Supabase configured: %s", config.supabase_ready)

    if not config.discord_ready:
        logger.error(
            "DISCORD_TOKEN is missing or placeholder. "
            "Set it in bot/.env (see .env.example) and restart."
        )

    bot = TriumphBot(config)

    # Start Flask health endpoint in a daemon thread (required for Render/UptimeRobot).
    start_health_server(config, bot_ref=bot)

    if not config.discord_ready:
        logger.warning(
            "Bot will not connect to Discord without a valid DISCORD_TOKEN. "
            "Health endpoint is running; configure token and restart."
        )
        # Keep process alive so /health remains reachable in local/dev checks.
        try:
            import time

            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Shutdown requested.")
            return 0

    try:
        bot.run(config.discord_token, log_handler=None, reconnect=True)
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
    except Exception:
        logger.exception("Bot crashed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
