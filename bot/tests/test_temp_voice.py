from __future__ import annotations

from services.temp_voice import DEFAULT_TEMPLATE, build_channel_name, normalize_limit


def test_default_template():
    assert (
        build_channel_name(None, user="Alice", display_name="Alice")
        == "Alice's Channel"
    )
    assert (
        build_channel_name(DEFAULT_TEMPLATE, user="Alice", display_name="Alice")
        == "Alice's Channel"
    )


def test_template_placeholders():
    name = build_channel_name(
        "{display_name} ({user})", user="alice", display_name="Alice"
    )
    assert name == "Alice (alice)"


def test_blank_template_falls_back():
    assert (
        build_channel_name("   ", user="Bob", display_name="Bobby")
        == "Bobby's Channel"
    )


def test_name_truncated_to_discord_limit():
    name = build_channel_name("{user}", user="x" * 150, display_name="x")
    assert len(name) == 100


def test_normalize_limit():
    assert normalize_limit(None) == 0
    assert normalize_limit(-5) == 0
    assert normalize_limit("12") == 12
    assert normalize_limit(500) == 99
    assert normalize_limit("abc") == 0
