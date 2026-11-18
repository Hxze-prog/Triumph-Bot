from __future__ import annotations

from services.automod_rules import (
    SpamTracker,
    contains_disallowed_link,
    contains_invite,
    extract_host,
    find_disallowed_links,
)


def test_invite_detection():
    assert contains_invite("join discord.gg/abc123")
    assert contains_invite("https://discord.com/invite/abc123")
    assert contains_invite("https://discordapp.com/invite/xyz")
    assert contains_invite("dsc.gg/test")
    assert not contains_invite("discord is a chat app")
    assert not contains_invite("https://discord.com/channels/1/2")


def test_link_detection_blocks_unknown_hosts():
    assert contains_disallowed_link("check https://example.com/page")
    assert contains_disallowed_link("www.evil.example/x")
    assert find_disallowed_links("https://example.com/a https://tenor.com/b") == [
        "https://example.com/a"
    ]


def test_link_allowlist_and_subdomains():
    assert not contains_disallowed_link("https://tenor.com/view/cat-123")
    assert not contains_disallowed_link("https://cdn.discordapp.com/attachments/1/2/a.png")
    assert not contains_disallowed_link("https://i.imgur.com/abc.png")
    assert not contains_disallowed_link("https://www.youtube.com/watch?v=abc")
    assert not contains_disallowed_link("no links in this message")


def test_extract_host():
    assert extract_host("https://www.Example.com/path") == "example.com"
    assert extract_host("https://tenor.com/view/x") == "tenor.com"
    assert extract_host("not-a-url") == ""


def test_spam_tracker_sliding_window():
    tracker = SpamTracker()
    key = (1, 2)
    assert not tracker.hit(key, now=100.0, threshold=3, interval=5)
    assert not tracker.hit(key, now=101.0, threshold=3, interval=5)
    assert tracker.hit(key, now=102.0, threshold=3, interval=5)
    tracker.reset(key)
    assert not tracker.hit(key, now=103.0, threshold=3, interval=5)


def test_spam_tracker_prunes_old_entries():
    tracker = SpamTracker()
    key = (1, 2)
    assert not tracker.hit(key, now=100.0, threshold=3, interval=5)
    assert not tracker.hit(key, now=101.0, threshold=3, interval=5)
    assert not tracker.hit(key, now=110.0, threshold=3, interval=5)
    assert not tracker.hit(key, now=111.0, threshold=3, interval=5)
    assert tracker.hit(key, now=112.0, threshold=3, interval=5)


def test_spam_tracker_prune_clears_inactive_keys():
    tracker = SpamTracker()
    tracker.hit((1, 2), now=100.0, threshold=5, interval=10)
    tracker.prune(now=200.0, interval=10)
    assert len(tracker) == 0
