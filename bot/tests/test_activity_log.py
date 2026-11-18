from __future__ import annotations

from types import SimpleNamespace

from services.activity_log import (
    LOG_EVENTS,
    display_user,
    event_keys,
    normalize_event,
    truncate,
)


def test_event_keys_cover_settings_columns():
    expected = {
        "join_leave",
        "message_delete",
        "message_edit",
        "role_change",
        "nickname_change",
        "voice",
        "moderation",
        "channel_events",
    }
    assert set(event_keys()) == expected
    for event in LOG_EVENTS.values():
        assert event.column.startswith("log_")
        assert event.column.endswith("_channel_id")


def test_normalize_event():
    assert normalize_event("message-delete").key == "message_delete"
    assert normalize_event(" Join_Leave ").key == "join_leave"
    assert normalize_event("unknown") is None
    assert normalize_event(None) is None


def test_truncate():
    assert truncate(None) == "*(empty)*"
    assert truncate("   ") == "*(empty)*"
    assert truncate("hello") == "hello"
    long = "x" * 1050
    result = truncate(long, limit=100)
    assert len(result) == 100
    assert result.endswith("...")


def test_display_user():
    user = SimpleNamespace(name="jojit", id=123)
    assert display_user(user) == "jojit (123)"
    assert display_user(SimpleNamespace(id=5)) == "5"
    assert display_user(None) == "Unknown"
