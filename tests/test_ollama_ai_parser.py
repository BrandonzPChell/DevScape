import pytest

from devscape.ollama_ai import _parse_content_to_move_and_dialogue


@pytest.mark.parametrize(
    "content, expected_move, expected_dialogue",
    [
        ("MOVE: [1,0] | SAY: I will advance.", {"dx": 1, "dy": 0}, "I will advance."),
        ("SAY: Hello there", None, "Hello there"),
        (
            "MOVE:[-2, 3] SAY: cautiously approach",
            {"dx": -2, "dy": 3},
            "cautiously approach",
        ),
        ("MOVE: 0,0", {"dx": 0, "dy": 0}, ""),  # no SAY; dialogue may be empty
        ("Completely unrelated text", None, "Completely unrelated text"),
        ("MOVE: [bad, data] SAY: fallback dialogue", None, "fallback dialogue"),
        ("", None, ""),  # empty content
        (None, None, ""),  # None content should be normalized
    ],
)
def test_parse_content_variants(content, expected_move, expected_dialogue):
    result = _parse_content_to_move_and_dialogue(content)
    assert isinstance(result, dict)
    assert "move" in result and "dialogue" in result
    assert result["move"] == expected_move
    assert result["dialogue"] == expected_dialogue
