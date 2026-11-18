from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from services import templates


def make_member() -> SimpleNamespace:
    now = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)
    guild = SimpleNamespace(name="Triumph HQ", member_count=42, members=[])
    return SimpleNamespace(
        mention="<@123>",
        name="alice",
        display_name="Alice",
        guild=guild,
        created_at=now - timedelta(days=400),
        joined_at=now - timedelta(days=10),
    )


def test_member_context_values() -> None:
    context = templates.member_context(
        make_member(), now=datetime(2026, 11, 19, 12, 0, tzinfo=UTC), member_number=7
    )
    assert context["user"] == "<@123>"
    assert context["display_name"] == "Alice"
    assert context["server"] == "Triumph HQ"
    assert context["member_count"] == "42"
    assert context["member_number"] == "7"
    assert context["created_at"] == "Oct 15, 2025"
    assert context["joined_at"] == "Nov 09, 2026"
    assert context["account_age"] == "1 year"


def test_member_number_unknown() -> None:
    context = templates.member_context(make_member())
    assert context["member_number"] == "?"


def test_render_replaces_known_placeholders() -> None:
    context = {"user": "<@1>", "server": "Guild", "member_number": "3"}
    assert (
        templates.render("Welcome {user} to {server} as #{member_number}!", context)
        == "Welcome <@1> to Guild as #3!"
    )


def test_render_leaves_unknown_placeholders() -> None:
    assert templates.render("Hello {unknown} {user}", {"user": "x"}) == "Hello {unknown} x"


def test_render_empty_template() -> None:
    assert templates.render(None, {}) == ""
    assert templates.render("", {}) == ""


def test_humanize_delta() -> None:
    assert templates.humanize_delta(timedelta(seconds=30)) == "less than a minute"
    assert templates.humanize_delta(timedelta(hours=2)) == "2 hours"
    assert templates.humanize_delta(timedelta(days=1)) == "1 day"
