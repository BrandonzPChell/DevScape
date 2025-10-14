import pytest

from src.devscape.ollama_ai import parse_move_and_dialogue


@pytest.mark.parametrize(
    "raw_input, expected_output",
    [
        (
            '{"message":{"content":"MOVE: up | SAY: I am going up"}}',
            {"move": {"dx": 0, "dy": -1}, "dialogue": "I am going up"},
        ),
        (
            '{"message":{"content":"SAY: Hello there"}}',
            {"move": {"dx": 0, "dy": 0}, "dialogue": "Hello there"},
        ),
        (
            '{"message":{"content":"MOVE: right"}}',
            {"move": {"dx": 1, "dy": 0}, "dialogue": ""},
        ),
        (
            '{"message":{"content":"MOVE: stay"}}',
            {"move": {"dx": 0, "dy": 0}, "dialogue": ""},
        ),
        (
            '{"message":{"content":"Some random text"}}',
            {"move": {"dx": 0, "dy": 0}, "dialogue": ""},
        ),
    ],
)
def test_parse_move_and_dialogue(raw_input, expected_output):
    assert parse_move_and_dialogue(raw_input) == expected_output
