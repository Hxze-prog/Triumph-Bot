from __future__ import annotations

from datetime import timedelta

from services.durations import (
    MAX_TIMEOUT,
    format_duration,
    format_seconds,
    parse_duration,
)


def test_parse_simple_units():
    assert parse_duration("10m") == timedelta(minutes=10)
    assert parse_duration("30s") == timedelta(seconds=30)
    assert parse_duration("2h") == timedelta(hours=2)
    assert parse_duration("3d") == timedelta(days=3)
    assert parse_duration("1w") == timedelta(weeks=1)


def test_parse_compound_and_spaces():
    assert parse_duration("1h30m") == timedelta(hours=1, minutes=30)
    assert parse_duration("2 days") == timedelta(days=2)
    assert parse_duration("1 hour, 15 minutes") == timedelta(hours=1, minutes=15)


def test_parse_bare_number_is_minutes():
    assert parse_duration("15") == timedelta(minutes=15)


def test_parse_invalid_values():
    assert parse_duration(None) is None
    assert parse_duration("") is None
    assert parse_duration("abc") is None
    assert parse_duration("10x") is None
    assert parse_duration("1h garbage") is None
    assert parse_duration("0m") is None


def test_capped_at_discord_maximum():
    assert parse_duration("60d") == MAX_TIMEOUT
    assert parse_duration("999999") == MAX_TIMEOUT


def test_format_helpers():
    assert format_duration(timedelta(hours=1, minutes=30)) == "1h 30m"
    assert format_duration(timedelta(days=1, seconds=5)) == "1d 5s"
    assert format_duration(timedelta(0)) == "0s"
    assert format_seconds(0) == "0s"
    assert format_seconds(90) == "1m 30s"
