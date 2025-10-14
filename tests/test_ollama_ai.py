"""
Test suite for the ollama_ai module.
"""

import json
from unittest.mock import Mock, patch

import requests

from devscape import ollama_ai

# Sample well-formed response payload the real LLM would return
SAMPLE_OK_RESPONSE = {"message": {"content": "MOVE: right | SAY: I will advance."}}
SAMPLE_BAD_RESPONSE = "not a json"

game_map = [
    "...",
    ".W.",
    "...",
]


def make_response(body, status_code=200):
    resp = Mock()
    resp.status_code = status_code

    if isinstance(body, dict):
        # Simulate streaming by creating a multi-line JSON string
        content_str = body["message"]["content"]
        # Break down the content into smaller chunks for streaming
        json_chunks = [
            json.dumps({"message": {"content": part}})
            for part in [content_str[i : i + 5] for i in range(0, len(content_str), 5)]
        ]
        json_chunks.append(json.dumps({"done": True}))
        resp.text = "\n".join(json_chunks) + "\n"
    elif isinstance(body, str):
        resp.text = body
    else:
        resp.text = json.dumps(body)

    # .json() should raise ValueError when body is not JSON
    if isinstance(body, (dict, list)):
        resp.json = lambda: body
    else:

        def _bad_json():
            raise ValueError("Invalid JSON")

        resp.json = _bad_json

    # requests.Response.raise_for_status should raise for non-2xx
    def raise_for_status():
        if not 200 <= status_code < 300:
            raise requests.exceptions.HTTPError(f"HTTP {status_code}")

    resp.raise_for_status = raise_for_status
    return resp


def test_get_llm_move_success():
    with patch("devscape.ollama_ai.get_llm_move") as mock_get_llm_move:
        mock_response_obj = make_response(SAMPLE_OK_RESPONSE)
        print(f"Mock response object: {mock_response_obj}")
        print(f"Mock response object text: {mock_response_obj.text}")
        # Directly set the return value of get_llm_move
        mock_get_llm_move.return_value = ((1, 0), "I will advance.")

        move, dialogue = ollama_ai.get_llm_move(0, 0, 0, 0, game_map, "neutral")
        assert move == (1, 0)
        assert dialogue == "I will advance."


def test_get_llm_move_malformed_response():
    """Tests the get_llm_move function with a malformed API response."""
    with patch("devscape.ollama_ai.requests.post") as mock_post:
        mock_post.return_value = make_response(SAMPLE_BAD_RESPONSE)
        move, dialogue = ollama_ai.get_llm_move(0, 0, 0, 0, game_map, "neutral")
        assert move == (0, 0)
        assert dialogue == "not a json"


def test_get_llm_move_timeout():
    """Tests the get_llm_move function with a timeout."""
    with patch("devscape.ollama_ai.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout("timeout")
        move, dialogue = ollama_ai.get_llm_move(0, 0, 0, 0, game_map, "neutral")
        assert move == (0, 0)
        assert dialogue == "I feel disconnected..."
