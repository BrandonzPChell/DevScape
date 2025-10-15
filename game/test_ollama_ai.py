"""
Tests for the Ollama AI client.
"""

import pytest
from ollama_ai import OllamaClient

@pytest.fixture
def client():
    """Returns an OllamaClient instance for testing."""
    return OllamaClient()

def test_parse_response_flexible(client):
    """Tests that _parse_response can handle flexible and malformed responses."""
    # Test case 1: Standard response
    response_text_1 = "MOVE: up | SAY: Hello there!"
    move, dialogue = client._parse_response(response_text_1)
    assert move == "up"
    assert dialogue == "Hello there!"

    # Test case 2: Extra whitespace
    response_text_2 = "  MOVE:  down   |  SAY:   I'm moving down.  "
    move, dialogue = client._parse_response(response_text_2)
    assert move == "down"
    assert dialogue == "I'm moving down."

    # Test case 3: Missing dialogue
    response_text_3 = "MOVE: left"
    move, dialogue = client._parse_response(response_text_3)
    assert move == "left"
    assert dialogue == "..."

    # Test case 4: Only dialogue
    response_text_4 = "SAY: I'll just stay here."
    move, dialogue = client._parse_response(response_text_4)
    assert move == "stay"
    assert dialogue == "I'll just stay here."

    # Test case 5: Malformed response
    response_text_5 = "I'm going right."
    move, dialogue = client._parse_response(response_text_5)
    assert move == "stay"
    assert dialogue == "..."

    # Test case 6: Reversed order
    response_text_6 = "SAY: I'm heading down! | MOVE: down"
    move, dialogue = client._parse_response(response_text_6)
    assert move == "down"
    assert dialogue == "I'm heading down!"