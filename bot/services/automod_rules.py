from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from urllib.parse import urlsplit

INVITE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"(?:discord\.gg|discord(?:app)?\.com/invite|discord\.me|dsc\.gg|invite\.gg)"
    r"/[A-Za-z0-9\-_]+",
    re.IGNORECASE,
)

URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>()\[\]{}]+", re.IGNORECASE)

ALLOWED_DOMAINS = frozenset(
    {
        "tenor.com",
        "giphy.com",
        "imgur.com",
        "cdn.discordapp.com",
        "media.discordapp.net",
        "youtube.com",
        "youtu.be",
        "spotify.com",
        "github.com",
        "twitch.tv",
        "klipy.com",
        "streamable.com",
        "wikimedia.org",
    }
)

_TRAILING_PUNCT = ".,!?;:'\""


def normalize_host(host: str | None) -> str:
    if not host:
        return ""
    value = host.strip().lower().rstrip(".")
    value = value.removeprefix("www.")
    return value


def extract_host(token: str) -> str:
    candidate = token.rstrip(_TRAILING_PUNCT)
    if candidate.startswith("www."):
        candidate = "http://" + candidate
    try:
        return normalize_host(urlsplit(candidate).hostname)
    except ValueError:
        return ""


def _is_allowed_host(host: str) -> bool:
    if not host:
        return False
    return any(host == domain or host.endswith("." + domain) for domain in ALLOWED_DOMAINS)


def contains_invite(content: str) -> bool:
    return bool(INVITE_RE.search(content or ""))


def find_disallowed_links(content: str) -> list[str]:
    """Return URLs whose host is not in the allowlist."""
    if not content:
        return []
    found: list[str] = []
    for match in URL_RE.finditer(content):
        token = match.group(0)
        host = extract_host(token)
        if host and not _is_allowed_host(host):
            found.append(token)
    return found


def contains_disallowed_link(content: str) -> bool:
    return bool(find_disallowed_links(content))


@dataclass
class SpamTracker:
    """Sliding-window message counter keyed by (guild_id, user_id)."""

    window: dict[tuple[int, int], deque[float]] = field(default_factory=dict)

    def hit(
        self,
        key: tuple[int, int],
        *,
        now: float,
        threshold: int,
        interval: float,
    ) -> bool:
        history = self.window.setdefault(key, deque())
        cutoff = now - max(interval, 0.0)
        while history and history[0] < cutoff:
            history.popleft()
        history.append(now)
        return len(history) >= max(threshold, 1)

    def reset(self, key: tuple[int, int]) -> None:
        self.window.pop(key, None)

    def prune(self, *, now: float, interval: float) -> None:
        cutoff = now - max(interval, 0.0)
        for key in list(self.window):
            history = self.window[key]
            while history and history[0] < cutoff:
                history.popleft()
            if not history:
                self.window.pop(key, None)

    def __len__(self) -> int:
        return len(self.window)
