from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


@dataclass
class TTLCache:
    """Simple in-memory TTL cache (per-key)."""

    ttl_seconds: float = 30.0
    _store: dict[Any, CacheEntry] = field(default_factory=dict)

    def get(self, key: Any) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at < time.monotonic():
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: Any, value: Any, ttl: float | None = None) -> None:
        seconds = self.ttl_seconds if ttl is None else ttl
        self._store[key] = CacheEntry(value=value, expires_at=time.monotonic() + seconds)

    def invalidate(self, key: Any) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
