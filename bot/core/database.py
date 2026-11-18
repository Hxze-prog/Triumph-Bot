from __future__ import annotations

import asyncio
import logging
from typing import Any

from supabase import Client, create_client

logger = logging.getLogger(__name__)


class Database:
    """Async-friendly wrapper around the Supabase client.

    Uses the service_role key (bot/server-side only). Supabase-py is synchronous,
    so blocking calls are executed via asyncio.to_thread.
    """

    def __init__(self, url: str | None, service_role_key: str | None) -> None:
        self._url = url
        self._key = service_role_key
        self._client: Client | None = None

    @property
    def configured(self) -> bool:
        return bool(
            self._url
            and self._key
            and self._url != "https://your-project-ref.supabase.co"
            and self._key != "your_supabase_service_role_key_here"
        )

    @property
    def client(self) -> Client | None:
        if not self.configured:
            return None
        if self._client is None:
            self._client = create_client(self._url, self._key)
        return self._client

    async def _run(self, func, /, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    def _ping_sync(self) -> tuple[bool, str]:
        if not self.configured:
            return False, "Supabase not configured (missing or placeholder credentials)."
        try:
            assert self.client is not None
            self.client.table("guilds").select("id").limit(1).execute()
            return True, "Supabase reachable (guilds table accessible)."
        except Exception as exc:  # noqa: BLE001 - return human-readable status
            msg = str(exc)
            if "relation" in msg and "does not exist" in msg:
                return True, "Supabase reachable (schema not applied yet)."
            if "Could not find the table" in msg or "PGRST205" in msg:
                return True, "Supabase reachable (schema not applied yet)."
            if "PGRST" in msg and "guilds" in msg:
                return True, "Supabase reachable (schema not applied yet)."
            logger.warning("Supabase ping failed: %s", msg)
            return False, f"Supabase check failed: {msg}"

    async def ping(self) -> tuple[bool, str]:
        """Best-effort connectivity check. Returns (ok, message)."""
        if not self.configured:
            return False, "Supabase not configured (missing or placeholder credentials)."
        try:
            return await self._run(self._ping_sync)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Supabase ping failed: %s", exc)
            return False, f"Supabase check failed: {exc}"

    def _get_guild_settings_sync(self, guild_id: int) -> dict[str, Any] | None:
        assert self.client is not None
        res = (
            self.client.table("guild_settings")
            .select("*")
            .eq("guild_id", guild_id)
            .limit(1)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def get_guild_settings(self, guild_id: int) -> dict[str, Any] | None:
        """Fetch guild_settings row for a guild, or None if unavailable/missing."""
        if not self.configured or guild_id is None:
            return None
        try:
            return await self._run(self._get_guild_settings_sync, guild_id)
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            if "schema not applied" in msg.lower() or "does not exist" in msg or "PGRST205" in msg:
                logger.debug("get_guild_settings unavailable (schema not applied?): %s", msg)
            else:
                logger.warning("get_guild_settings failed for guild %s: %s", guild_id, msg)
            return None

    def _upsert_guild_settings_sync(self, guild_id: int, values: dict[str, Any]) -> dict[str, Any] | None:
        assert self.client is not None
        payload = {"guild_id": guild_id, **values}
        res = self.client.table("guild_settings").upsert(payload).execute()
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def upsert_guild_settings(self, guild_id: int, values: dict[str, Any]) -> dict[str, Any] | None:
        """Upsert guild_settings for a guild. Returns row or None on failure."""
        if not self.configured or guild_id is None:
            return None
        try:
            return await self._run(self._upsert_guild_settings_sync, guild_id, values)
        except Exception as exc:  # noqa: BLE001
            logger.warning("upsert_guild_settings failed for guild %s: %s", guild_id, exc)
            return None

    def _next_member_number_sync(self, guild_id: int) -> int | None:
        assert self.client is not None
        res = self.client.rpc("next_member_number", {"p_guild_id": guild_id}).execute()
        data = getattr(res, "data", None)
        if isinstance(data, int):
            return data
        if isinstance(data, float):
            return int(data)
        if isinstance(data, list) and data:
            value = data[0]
            if isinstance(value, int):
                return value
            if isinstance(value, dict):
                for candidate in value.values():
                    if isinstance(candidate, int):
                        return candidate
        if isinstance(data, dict):
            for candidate in data.values():
                if isinstance(candidate, int):
                    return candidate
        return None

    async def next_member_number(self, guild_id: int) -> int | None:
        """Atomically increment and return the guild member counter."""
        if not self.configured or guild_id is None:
            return None
        try:
            return await self._run(self._next_member_number_sync, guild_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("next_member_number failed for guild %s: %s", guild_id, exc)
            return None

    def _get_member_sync(self, guild_id: int, user_id: int) -> dict[str, Any] | None:
        assert self.client is not None
        res = (
            self.client.table("members")
            .select("*")
            .eq("guild_id", guild_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def get_member(self, guild_id: int, user_id: int) -> dict[str, Any] | None:
        """Fetch a member record for a guild, or None if unavailable/missing."""
        if not self.configured or guild_id is None or user_id is None:
            return None
        try:
            return await self._run(self._get_member_sync, guild_id, user_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("get_member failed for %s/%s: %s", guild_id, user_id, exc)
            return None

    def _upsert_member_sync(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        assert self.client is not None
        res = self.client.table("members").upsert(payload).execute()
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def upsert_member(self, guild_id: int, user_id: int, values: dict[str, Any]) -> dict[str, Any] | None:
        """Upsert a member record. Returns the stored row or None on failure."""
        if not self.configured or guild_id is None or user_id is None:
            return None
        payload = {"guild_id": guild_id, "user_id": user_id, **values}
        try:
            return await self._run(self._upsert_member_sync, payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("upsert_member failed for %s/%s: %s", guild_id, user_id, exc)
            return None

    def _update_member_sync(self, guild_id: int, user_id: int, values: dict[str, Any]) -> dict[str, Any] | None:
        assert self.client is not None
        res = (
            self.client.table("members")
            .update(values)
            .eq("guild_id", guild_id)
            .eq("user_id", user_id)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def update_member(self, guild_id: int, user_id: int, values: dict[str, Any]) -> dict[str, Any] | None:
        """Update fields on an existing member record (no insert)."""
        if not self.configured or guild_id is None or user_id is None:
            return None
        try:
            return await self._run(self._update_member_sync, guild_id, user_id, values)
        except Exception as exc:  # noqa: BLE001
            logger.warning("update_member failed for %s/%s: %s", guild_id, user_id, exc)
            return None

    async def set_member_left(self, guild_id: int, user_id: int, left_at: str) -> dict[str, Any] | None:
        """Mark a member record as having left the guild."""
        return await self.update_member(guild_id, user_id, {"left_at": left_at})

    def _upsert_guild_sync(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        assert self.client is not None
        res = self.client.table("guilds").upsert(payload).execute()
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def upsert_guild(
        self,
        guild_id: int,
        *,
        name: str | None = None,
        icon_url: str | None = None,
        owner_id: int | None = None,
    ) -> dict[str, Any] | None:
        """Keep the guilds row fresh (name/icon/owner)."""
        if not self.configured or guild_id is None:
            return None
        payload = {"id": guild_id}
        if name is not None:
            payload["name"] = name
        if icon_url is not None:
            payload["icon_url"] = icon_url
        if owner_id is not None:
            payload["owner_id"] = owner_id
        try:
            return await self._run(self._upsert_guild_sync, payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("upsert_guild failed for guild %s: %s", guild_id, exc)
            return None

    def _add_warning_sync(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        assert self.client is not None
        res = self.client.table("warnings").insert(payload).execute()
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def add_warning(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int | None,
        reason: str,
    ) -> dict[str, Any] | None:
        """Insert an active warning for a member."""
        if not self.configured or guild_id is None or user_id is None:
            return None
        payload = {
            "guild_id": guild_id,
            "user_id": user_id,
            "moderator_id": moderator_id,
            "reason": reason,
        }
        try:
            return await self._run(self._add_warning_sync, payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("add_warning failed for %s/%s: %s", guild_id, user_id, exc)
            return None

    def _list_warnings_sync(
        self,
        guild_id: int,
        user_id: int,
        active_only: bool,
        limit: int,
    ) -> list[dict[str, Any]]:
        assert self.client is not None
        query = (
            self.client.table("warnings")
            .select("*")
            .eq("guild_id", guild_id)
            .eq("user_id", user_id)
        )
        if active_only:
            query = query.eq("active", True)
        res = query.order("created_at", desc=True).limit(limit).execute()
        data = getattr(res, "data", None) or []
        return [row for row in data if isinstance(row, dict)]

    async def list_warnings(
        self,
        guild_id: int,
        user_id: int,
        *,
        active_only: bool = True,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """List warnings for a member, newest first."""
        if not self.configured or guild_id is None or user_id is None:
            return []
        try:
            return await self._run(
                self._list_warnings_sync, guild_id, user_id, active_only, max(1, limit)
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("list_warnings failed for %s/%s: %s", guild_id, user_id, exc)
            return []

    def _get_warning_sync(self, guild_id: int, warning_id: int) -> dict[str, Any] | None:
        assert self.client is not None
        res = (
            self.client.table("warnings")
            .select("*")
            .eq("guild_id", guild_id)
            .eq("id", warning_id)
            .limit(1)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def get_warning(self, guild_id: int, warning_id: int) -> dict[str, Any] | None:
        if not self.configured or guild_id is None or warning_id is None:
            return None
        try:
            return await self._run(self._get_warning_sync, guild_id, warning_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("get_warning failed for %s/%s: %s", guild_id, warning_id, exc)
            return None

    def _deactivate_warning_sync(
        self, guild_id: int, warning_id: int
    ) -> dict[str, Any] | None:
        assert self.client is not None
        res = (
            self.client.table("warnings")
            .update({"active": False})
            .eq("guild_id", guild_id)
            .eq("id", warning_id)
            .eq("active", True)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def deactivate_warning(
        self, guild_id: int, warning_id: int
    ) -> dict[str, Any] | None:
        """Mark a warning inactive. Returns the updated row or None."""
        if not self.configured or guild_id is None or warning_id is None:
            return None
        try:
            return await self._run(
                self._deactivate_warning_sync, guild_id, warning_id
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "deactivate_warning failed for %s/%s: %s", guild_id, warning_id, exc
            )
            return None

    def _count_active_warnings_sync(self, guild_id: int, user_id: int) -> int:
        assert self.client is not None
        res = (
            self.client.table("warnings")
            .select("id", count="exact")
            .eq("guild_id", guild_id)
            .eq("user_id", user_id)
            .eq("active", True)
            .execute()
        )
        count = getattr(res, "count", None)
        return int(count) if count is not None else len(getattr(res, "data", None) or [])

    async def count_active_warnings(self, guild_id: int, user_id: int) -> int:
        if not self.configured or guild_id is None or user_id is None:
            return 0
        try:
            return await self._run(self._count_active_warnings_sync, guild_id, user_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "count_active_warnings failed for %s/%s: %s", guild_id, user_id, exc
            )
            return 0

    def _add_moderation_log_sync(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        assert self.client is not None
        res = self.client.table("moderation_logs").insert(payload).execute()
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def add_moderation_log(
        self,
        guild_id: int,
        action: str,
        *,
        target_id: int | None = None,
        moderator_id: int | None = None,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Insert a moderation history entry."""
        if not self.configured or guild_id is None:
            return None
        payload = {
            "guild_id": guild_id,
            "action": action,
            "target_id": target_id,
            "moderator_id": moderator_id,
            "reason": reason,
            "metadata": metadata or {},
        }
        try:
            return await self._run(self._add_moderation_log_sync, payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "add_moderation_log failed for %s/%s: %s", guild_id, action, exc
            )
            return None

    def _list_moderation_logs_sync(
        self, guild_id: int, target_id: int | None, limit: int
    ) -> list[dict[str, Any]]:
        assert self.client is not None
        query = self.client.table("moderation_logs").select("*").eq("guild_id", guild_id)
        if target_id is not None:
            query = query.eq("target_id", target_id)
        res = query.order("created_at", desc=True).limit(limit).execute()
        data = getattr(res, "data", None) or []
        return [row for row in data if isinstance(row, dict)]

    async def list_moderation_logs(
        self,
        guild_id: int,
        *,
        target_id: int | None = None,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """List moderation history, newest first (optionally for one target)."""
        if not self.configured or guild_id is None:
            return []
        try:
            return await self._run(
                self._list_moderation_logs_sync, guild_id, target_id, max(1, limit)
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("list_moderation_logs failed for %s: %s", guild_id, exc)
            return []

    def _add_reaction_role_sync(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        assert self.client is not None
        res = self.client.table("reaction_roles").insert(payload).execute()
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def add_reaction_role(
        self,
        guild_id: int,
        message_id: int,
        channel_id: int,
        emoji: str,
        role_id: int,
    ) -> dict[str, Any] | None:
        """Create a reaction-role mapping (unique per message+emoji)."""
        if not self.configured or guild_id is None:
            return None
        payload = {
            "guild_id": guild_id,
            "message_id": message_id,
            "channel_id": channel_id,
            "emoji": emoji,
            "role_id": role_id,
        }
        try:
            return await self._run(self._add_reaction_role_sync, payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "add_reaction_role failed for %s/%s: %s", message_id, emoji, exc
            )
            return None

    def _get_reaction_role_sync(
        self, message_id: int, emoji: str
    ) -> dict[str, Any] | None:
        assert self.client is not None
        res = (
            self.client.table("reaction_roles")
            .select("*")
            .eq("message_id", message_id)
            .eq("emoji", emoji)
            .limit(1)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def get_reaction_role(
        self, message_id: int, emoji: str
    ) -> dict[str, Any] | None:
        if not self.configured or message_id is None:
            return None
        try:
            return await self._run(self._get_reaction_role_sync, message_id, emoji)
        except Exception as exc:  # noqa: BLE001
            logger.warning("get_reaction_role failed for %s: %s", message_id, exc)
            return None

    def _list_reaction_roles_sync(self, guild_id: int) -> list[dict[str, Any]]:
        assert self.client is not None
        res = (
            self.client.table("reaction_roles")
            .select("*")
            .eq("guild_id", guild_id)
            .order("id")
            .execute()
        )
        data = getattr(res, "data", None) or []
        return [row for row in data if isinstance(row, dict)]

    async def list_reaction_roles(self, guild_id: int) -> list[dict[str, Any]]:
        if not self.configured or guild_id is None:
            return []
        try:
            return await self._run(self._list_reaction_roles_sync, guild_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("list_reaction_roles failed for %s: %s", guild_id, exc)
            return []

    async def remove_reaction_role(
        self, guild_id: int, message_id: int, emoji: str
    ) -> bool:
        """Delete a mapping. Returns True when a row was removed."""
        if not self.configured or guild_id is None:
            return False

        def run() -> bool:
            assert self.client is not None
            res = (
                self.client.table("reaction_roles")
                .delete()
                .eq("guild_id", guild_id)
                .eq("message_id", message_id)
                .eq("emoji", emoji)
                .execute()
            )
            return bool(getattr(res, "data", None))

        try:
            return await self._run(run)
        except Exception as exc:  # noqa: BLE001
            logger.warning("remove_reaction_role failed for %s: %s", message_id, exc)
            return False

    async def delete_reaction_roles_for_message(self, message_id: int) -> int:
        """Drop every mapping attached to a deleted message."""
        if not self.configured or message_id is None:
            return 0

        def run() -> int:
            assert self.client is not None
            res = (
                self.client.table("reaction_roles")
                .delete()
                .eq("message_id", message_id)
                .execute()
            )
            return len(getattr(res, "data", None) or [])

        try:
            return await self._run(run)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "delete_reaction_roles_for_message failed for %s: %s", message_id, exc
            )
            return 0

    def _upsert_temp_voice_sync(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        assert self.client is not None
        res = self.client.table("temp_voice_channels").upsert(payload).execute()
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def upsert_temp_voice_channel(
        self,
        channel_id: int,
        guild_id: int,
        owner_id: int,
        *,
        channel_name: str | None = None,
        user_limit: int = 0,
        is_locked: bool = False,
    ) -> dict[str, Any] | None:
        """Record a temporary voice channel (channel_id is the primary key)."""
        if not self.configured or channel_id is None or guild_id is None:
            return None
        payload: dict[str, Any] = {
            "channel_id": channel_id,
            "guild_id": guild_id,
            "owner_id": owner_id,
            "user_limit": user_limit,
            "is_locked": is_locked,
            "deleted_at": None,
        }
        if channel_name is not None:
            payload["channel_name"] = channel_name
        try:
            return await self._run(self._upsert_temp_voice_sync, payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "upsert_temp_voice_channel failed for %s: %s", channel_id, exc
            )
            return None

    def _get_temp_voice_sync(self, channel_id: int) -> dict[str, Any] | None:
        assert self.client is not None
        res = (
            self.client.table("temp_voice_channels")
            .select("*")
            .eq("channel_id", channel_id)
            .limit(1)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def get_temp_voice_channel(self, channel_id: int) -> dict[str, Any] | None:
        if not self.configured or channel_id is None:
            return None
        try:
            return await self._run(self._get_temp_voice_sync, channel_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("get_temp_voice_channel failed for %s: %s", channel_id, exc)
            return None

    def _list_temp_voice_sync(
        self, guild_id: int, active_only: bool
    ) -> list[dict[str, Any]]:
        assert self.client is not None
        query = (
            self.client.table("temp_voice_channels")
            .select("*")
            .eq("guild_id", guild_id)
        )
        if active_only:
            query = query.is_("deleted_at", "null")
        res = query.order("created_at", desc=True).execute()
        data = getattr(res, "data", None) or []
        return [row for row in data if isinstance(row, dict)]

    async def list_temp_voice_channels(
        self, guild_id: int, *, active_only: bool = True
    ) -> list[dict[str, Any]]:
        if not self.configured or guild_id is None:
            return []
        try:
            return await self._run(self._list_temp_voice_sync, guild_id, active_only)
        except Exception as exc:  # noqa: BLE001
            logger.warning("list_temp_voice_channels failed for %s: %s", guild_id, exc)
            return []

    async def update_temp_voice_channel(
        self, channel_id: int, values: dict[str, Any]
    ) -> dict[str, Any] | None:
        if not self.configured or channel_id is None:
            return None

        def run() -> dict[str, Any] | None:
            assert self.client is not None
            res = (
                self.client.table("temp_voice_channels")
                .update(values)
                .eq("channel_id", channel_id)
                .execute()
            )
            data = getattr(res, "data", None) or []
            if not data:
                return None
            row = data[0]
            return row if isinstance(row, dict) else None

        try:
            return await self._run(run)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "update_temp_voice_channel failed for %s: %s", channel_id, exc
            )
            return None

    async def mark_temp_voice_deleted(
        self, channel_id: int, deleted_at: str
    ) -> dict[str, Any] | None:
        return await self.update_temp_voice_channel(
            channel_id, {"deleted_at": deleted_at}
        )

    def _create_poll_sync(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        assert self.client is not None
        res = self.client.table("polls").insert(payload).execute()
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def create_poll(
        self,
        guild_id: int,
        channel_id: int,
        question: str,
        options: list[str],
        *,
        created_by: int | None = None,
        ends_at: str | None = None,
    ) -> dict[str, Any] | None:
        if not self.configured or guild_id is None:
            return None
        payload = {
            "guild_id": guild_id,
            "channel_id": channel_id,
            "question": question,
            "options": options,
            "created_by": created_by,
            "ends_at": ends_at,
        }
        try:
            return await self._run(self._create_poll_sync, payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("create_poll failed for %s: %s", guild_id, exc)
            return None

    async def set_poll_message(
        self, guild_id: int, poll_id: int, message_id: int
    ) -> dict[str, Any] | None:
        if not self.configured or poll_id is None:
            return None

        def run() -> dict[str, Any] | None:
            assert self.client is not None
            res = (
                self.client.table("polls")
                .update({"message_id": message_id})
                .eq("guild_id", guild_id)
                .eq("id", poll_id)
                .execute()
            )
            data = getattr(res, "data", None) or []
            if not data:
                return None
            row = data[0]
            return row if isinstance(row, dict) else None

        try:
            return await self._run(run)
        except Exception as exc:  # noqa: BLE001
            logger.warning("set_poll_message failed for poll %s: %s", poll_id, exc)
            return None

    def _get_poll_sync(
        self, guild_id: int, message_id: int
    ) -> dict[str, Any] | None:
        assert self.client is not None
        res = (
            self.client.table("polls")
            .select("*")
            .eq("guild_id", guild_id)
            .eq("message_id", message_id)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def get_poll(
        self, guild_id: int, message_id: int
    ) -> dict[str, Any] | None:
        if not self.configured or message_id is None:
            return None
        try:
            return await self._run(self._get_poll_sync, guild_id, message_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("get_poll failed for %s: %s", message_id, exc)
            return None

    async def close_poll(
        self, guild_id: int, message_id: int
    ) -> dict[str, Any] | None:
        if not self.configured or message_id is None:
            return None

        def run() -> dict[str, Any] | None:
            assert self.client is not None
            res = (
                self.client.table("polls")
                .update({"closed": True})
                .eq("guild_id", guild_id)
                .eq("message_id", message_id)
                .execute()
            )
            data = getattr(res, "data", None) or []
            if not data:
                return None
            row = data[0]
            return row if isinstance(row, dict) else None

        try:
            return await self._run(run)
        except Exception as exc:  # noqa: BLE001
            logger.warning("close_poll failed for %s: %s", message_id, exc)
            return None

    async def add_server_stats(
        self, guild_id: int, values: dict[str, Any]
    ) -> dict[str, Any] | None:
        if not self.configured or guild_id is None:
            return None

        def run() -> dict[str, Any] | None:
            assert self.client is not None
            res = (
                self.client.table("server_stats")
                .insert({"guild_id": guild_id, **values})
                .execute()
            )
            data = getattr(res, "data", None) or []
            if not data:
                return None
            row = data[0]
            return row if isinstance(row, dict) else None

        try:
            return await self._run(run)
        except Exception as exc:  # noqa: BLE001
            logger.warning("add_server_stats failed for %s: %s", guild_id, exc)
            return None

    def _list_server_stats_sync(
        self, guild_id: int, limit: int
    ) -> list[dict[str, Any]]:
        assert self.client is not None
        res = (
            self.client.table("server_stats")
            .select("*")
            .eq("guild_id", guild_id)
            .order("recorded_at", desc=True)
            .limit(limit)
            .execute()
        )
        data = getattr(res, "data", None) or []
        return [row for row in data if isinstance(row, dict)]

    async def list_server_stats(
        self, guild_id: int, *, limit: int = 10
    ) -> list[dict[str, Any]]:
        if not self.configured or guild_id is None:
            return []
        try:
            return await self._run(self._list_server_stats_sync, guild_id, max(1, limit))
        except Exception as exc:  # noqa: BLE001
            logger.warning("list_server_stats failed for %s: %s", guild_id, exc)
            return []

    # ------------------------------------------------------------------
    # Activity logs (Phase 8)
    # ------------------------------------------------------------------

    def _add_activity_log_sync(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        assert self.client is not None
        res = self.client.table("activity_logs").insert(payload).execute()
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def add_activity_log(
        self,
        guild_id: int,
        event_type: str,
        *,
        actor_id: int | None = None,
        target_id: int | None = None,
        channel_id: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Insert an activity/audit log entry."""
        if not self.configured or guild_id is None:
            return None
        record = {
            "guild_id": guild_id,
            "event_type": event_type,
            "actor_id": actor_id,
            "target_id": target_id,
            "channel_id": channel_id,
            "payload": payload or {},
        }
        try:
            return await self._run(self._add_activity_log_sync, record)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "add_activity_log failed for %s/%s: %s", guild_id, event_type, exc
            )
            return None

    def _list_activity_logs_sync(
        self, guild_id: int, event_type: str | None, limit: int
    ) -> list[dict[str, Any]]:
        assert self.client is not None
        query = self.client.table("activity_logs").select("*").eq("guild_id", guild_id)
        if event_type:
            query = query.eq("event_type", event_type)
        res = query.order("created_at", desc=True).limit(limit).execute()
        data = getattr(res, "data", None) or []
        return [row for row in data if isinstance(row, dict)]

    async def list_activity_logs(
        self,
        guild_id: int,
        *,
        event_type: str | None = None,
        limit: int = 15,
    ) -> list[dict[str, Any]]:
        """List stored activity logs, newest first."""
        if not self.configured or guild_id is None:
            return []
        try:
            return await self._run(
                self._list_activity_logs_sync, guild_id, event_type, max(1, limit)
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("list_activity_logs failed for %s: %s", guild_id, exc)
            return []

    # ------------------------------------------------------------------
    # Automations (Phase 9)
    # ------------------------------------------------------------------

    def _add_automation_sync(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        assert self.client is not None
        res = self.client.table("automations").insert(payload).execute()
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def add_automation(
        self,
        guild_id: int,
        automation_type: str,
        name: str,
        *,
        channel_id: int | None = None,
        cron: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create an automation row."""
        if not self.configured or guild_id is None:
            return None
        record = {
            "guild_id": guild_id,
            "type": automation_type,
            "name": name,
            "channel_id": channel_id,
            "cron": cron,
            "payload": payload or {},
            "enabled": True,
        }
        try:
            return await self._run(self._add_automation_sync, record)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "add_automation failed for %s/%s: %s", guild_id, name, exc
            )
            return None

    def _get_automation_sync(self, automation_id: int) -> dict[str, Any] | None:
        assert self.client is not None
        res = (
            self.client.table("automations")
            .select("*")
            .eq("id", automation_id)
            .limit(1)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def get_automation(self, automation_id: int) -> dict[str, Any] | None:
        if not self.configured or automation_id is None:
            return None
        try:
            return await self._run(self._get_automation_sync, automation_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("get_automation failed for %s: %s", automation_id, exc)
            return None

    def _list_automations_sync(
        self,
        guild_id: int | None,
        automation_type: str | None,
        enabled_only: bool,
    ) -> list[dict[str, Any]]:
        assert self.client is not None
        query = self.client.table("automations").select("*")
        if guild_id is not None:
            query = query.eq("guild_id", guild_id)
        if automation_type:
            query = query.eq("type", automation_type)
        if enabled_only:
            query = query.eq("enabled", True)
        res = query.order("id").execute()
        data = getattr(res, "data", None) or []
        return [row for row in data if isinstance(row, dict)]

    async def list_automations(
        self,
        guild_id: int | None,
        *,
        automation_type: str | None = None,
        enabled_only: bool = False,
    ) -> list[dict[str, Any]]:
        """List automations (all guilds when guild_id is None)."""
        if not self.configured:
            return []
        try:
            return await self._run(
                self._list_automations_sync, guild_id, automation_type, enabled_only
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("list_automations failed for %s: %s", guild_id, exc)
            return []

    def _update_automation_sync(
        self, automation_id: int, values: dict[str, Any]
    ) -> dict[str, Any] | None:
        assert self.client is not None
        res = (
            self.client.table("automations")
            .update(values)
            .eq("id", automation_id)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if not data:
            return None
        row = data[0]
        return row if isinstance(row, dict) else None

    async def update_automation(
        self, automation_id: int, values: dict[str, Any]
    ) -> dict[str, Any] | None:
        if not self.configured or automation_id is None:
            return None
        try:
            return await self._run(self._update_automation_sync, automation_id, values)
        except Exception as exc:  # noqa: BLE001
            logger.warning("update_automation failed for %s: %s", automation_id, exc)
            return None

    async def delete_automation(self, automation_id: int) -> bool:
        if not self.configured or automation_id is None:
            return False

        def run() -> bool:
            assert self.client is not None
            res = (
                self.client.table("automations")
                .delete()
                .eq("id", automation_id)
                .execute()
            )
            return bool(getattr(res, "data", None))

        try:
            return await self._run(run)
        except Exception as exc:  # noqa: BLE001
            logger.warning("delete_automation failed for %s: %s", automation_id, exc)
            return False

    async def mark_automation_run(
        self, automation_id: int, ran_at: str
    ) -> dict[str, Any] | None:
        return await self.update_automation(automation_id, {"last_run_at": ran_at})
