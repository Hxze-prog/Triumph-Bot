from __future__ import annotations

from types import SimpleNamespace

from services.automations import (
    AUTOMATION_TYPES,
    chunk_message,
    is_scheduled,
    normalize_type,
    render_message,
    response_matches,
    validate_cron,
)


def test_validate_cron():
    assert validate_cron("0 9 * * *")
    assert validate_cron("*/15 * * * *")
    assert validate_cron("30 8 * * 1-5")
    assert not validate_cron("")
    assert not validate_cron("not a cron")
    assert not validate_cron("0 9 * *")


def test_normalize_type():
    assert normalize_type("welcome") == "welcome"
    assert normalize_type("Announcement") == "announcement"
    assert normalize_type("auto-role") == "autorole"
    assert normalize_type("nope") is None
    assert normalize_type(None) is None


def test_is_scheduled():
    assert is_scheduled("announcement")
    assert is_scheduled("stats")
    assert not is_scheduled("autorole")
    assert not is_scheduled("response")
    assert set(AUTOMATION_TYPES) >= {
        "announcement",
        "message",
        "reminder",
        "stats",
        "autorole",
        "welcome",
        "goodbye",
        "response",
    }


def test_chunk_message():
    assert chunk_message("") == []
    assert chunk_message("hello") == ["hello"]
    long = "a" * 4500
    chunks = chunk_message(long, limit=2000)
    assert all(len(chunk) <= 2000 for chunk in chunks)
    assert "".join(chunks) == long

    lines = "\n".join(["line"] * 500)
    chunks = chunk_message(lines, limit=100)
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_render_message_placeholders():
    guild = SimpleNamespace(name="Triumph", member_count=42)
    member = SimpleNamespace(name="jojit", display_name="Jojit", mention="<@1>")
    rendered = render_message(
        "{guild}: {member_count} | {user} ({display_name}) {mention} {unknown}",
        guild=guild,
        member=member,
    )
    assert rendered == "Triumph: 42 | jojit (Jojit) <@1> {unknown}"
    assert render_message(None) == ""
    assert render_message("{guild}", guild=None) == ""


def test_response_matches():
    payload = {"trigger": "hello|free nitro"}
    assert response_matches(payload, "well HELLO there")
    assert response_matches(payload, "get FREE NITRO now")
    assert not response_matches(payload, "unrelated")
    assert not response_matches({}, "hello")
