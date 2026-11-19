from __future__ import annotations

import pytest

from services.polls import (
    MAX_OPTIONS,
    NUMBER_EMOJIS,
    normalize_emoji,
    parse_poll_body,
    poll_embed,
)


def test_parse_poll_body():
    question, options = parse_poll_body("Best map? | Dust | Mirage | Inferno")
    assert question == "Best map?"
    assert options == ["Dust", "Mirage", "Inferno"]


def test_parse_poll_body_strips_and_ignores_empty_parts():
    question, options = parse_poll_body("Q | A |  | B ")
    assert question == "Q"
    assert options == ["A", "B"]


@pytest.mark.parametrize(
    "body",
    [
        "",
        "Only a question",
        "Question | Only one option",
        "Question | A | B | C | D | E | F | G | H | I | J | K",
        " | A | B",
    ],
)
def test_parse_poll_body_rejects_invalid(body):
    with pytest.raises(ValueError):
        parse_poll_body(body)


def test_number_emoji_count():
    assert len(NUMBER_EMOJIS) == MAX_OPTIONS == 10


def test_normalize_keycap_emoji():
    assert normalize_emoji("1\ufe0f\u20e3") == normalize_emoji("1\u20e3")


def test_poll_embed_lists_options():
    embed = poll_embed("Pick", ["A", "B"], "tester")
    assert embed.title == "Pick"
    assert "A" in (embed.description or "")
    assert "B" in (embed.description or "")
    assert embed.footer.text == "Poll by tester"
