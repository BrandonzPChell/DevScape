"""
Test suite for the ollama_ai module's requests handling.
"""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from devscape import ollama_ai


# Helper to build a fake Response-like object used by requests.post mocks
def make_response(body, status_code=200):
    resp = Mock()
    resp.status_code = status_code
    # .text used when JSON decode fails
    resp.text = body if isinstance(body, str) else json.dumps(body)
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


@pytest.fixture
def client():
    # instantiate the Ollama client as used in your codebase
    # adapt constructor args if your OllamaClient requires different params
    return ollama_ai.OllamaClient(api_url="http://example.local", model="test-model")


def test_send_request_success_returns_content(client):
    # Well-formed JSON with nested message.content path expected by _send_request
    payload = {"message": {"content": "MOVE: [1,0] | SAY: I will advance."}}
    resp = make_response(payload, status_code=200)

    with patch("devscape.ollama_ai.requests.post", return_value=resp) as mock_post:
        result = client._send_request(messages=[{"role": "user", "content": "state"}])  # pylint: disable=protected-access
        assert isinstance(result, dict)
        assert "move" in result and "dialogue" in result and "raw" in result
        assert result["dialogue"] == "I will advance."
        assert result["move"] == {"dx": 1, "dy": 0}
        mock_post.assert_called_once()


def test_send_request_malformed_json_returns_text(client):
    # Body is not valid JSON; _send_request should return response.text.strip()
    body_text = "NOT JSON - raw response from LLM"
    resp = make_response(body_text, status_code=200)

    with patch("devscape.ollama_ai.requests.post", return_value=resp) as mock_post:
        result = client._send_request(messages=[{"role": "user", "content": "state"}])  # pylint: disable=protected-access
        assert isinstance(result, dict)
        assert "move" in result and "dialogue" in result and "raw" in result
        assert result["dialogue"] == body_text.strip()
        assert result["move"] is None
        mock_post.assert_called_once()


def test_send_request_http_error_uses_fallback(client):
    # Simulate non-2xx HTTP status -> raise_for_status triggers RequestException path
    resp = make_response({"error": "server error"}, status_code=500)

    with patch("devscape.ollama_ai.requests.post", return_value=resp) as mock_post:
        # Because resp.raise_for_status raises HTTPError, the client._send_request should catch and
        # return the friendly fallback string "I feel disconnected..."
        result = client._send_request(messages=[{"role": "user", "content": "state"}])  # pylint: disable=protected-access
        assert isinstance(result, dict)
        assert result["move"] == {"dx": 0, "dy": 0}
        mock_post.assert_called_once()
