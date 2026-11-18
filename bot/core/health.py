from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime
from typing import Any

from config import Config
from flask import Flask, jsonify

logger = logging.getLogger(__name__)


def create_health_app(config: Config, bot_ref: Any | None = None) -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index() -> tuple[Any, int]:
        return jsonify({"service": "Triumph-bot", "status": "running"}), 200

    @app.get("/health")
    def health() -> tuple[Any, int]:
        bot_ready = False
        guilds = 0
        if bot_ref is not None:
            try:
                bot_ready = bool(getattr(bot_ref, "is_ready", lambda: False)())
                guilds = len(getattr(bot_ref, "guilds", []))
            except Exception:  # noqa: BLE001
                bot_ready = False
        return (
            jsonify(
                {
                    "status": "ok",
                    "time": datetime.now(UTC).isoformat(),
                    "bot_ready": bot_ready,
                    "guilds": guilds,
                    "supabase_configured": config.supabase_ready,
                    "discord_configured": config.discord_ready,
                }
            ),
            200,
        )

    return app


def start_health_server(config: Config, bot_ref: Any | None = None) -> threading.Thread:
    app = create_health_app(config, bot_ref)

    def _run() -> None:
        # Use Flask's built-in server; sufficient for a simple health endpoint on Render.
        logger.info("Starting health server on %s:%s", config.host, config.port)
        app.run(host=config.host, port=config.port, use_reloader=False)

    thread = threading.Thread(target=_run, name="health-server", daemon=True)
    thread.start()
    return thread
