from types import SimpleNamespace
from unittest.mock import patch

import pytest
import requests

from devscape import ollama_ai


@pytest.fixture
def mock_requests_post():
    """Fixture to mock requests.post."""
    with patch("requests.post") as mock_post:
        yield mock_post


def test_ollama_client_send_request_success(mock_requests_post):
    client = ollama_ai.OllamaClient(api_url="http://fake-url", model="fake-model")
    mock_response = SimpleNamespace(
        text='{"message": {"content": "hello from AI"}}',
        status_code=200,
        json=lambda: {"message": {"content": "hello from AI"}},
        raise_for_status=lambda: None,
    )
    mock_requests_post.return_value = mock_response
    out = client._send_request([{"role": "user", "content": "test"}])  # pylint: disable=protected-access

    assert isinstance(out, dict)
    assert "hello from AI" in out["dialogue"]
    mock_requests_post.assert_called_once()


def test_ollama_client_send_request_non200_raises(mock_requests_post):
    """
    Tests that _send_request handles non-200 responses by raising HTTPError.
    """

    def mock_raise_for_status():
        raise requests.exceptions.HTTPError("500 Server Error")

    mock_response = SimpleNamespace(
        text="oops",
        status_code=500,
        raise_for_status=mock_raise_for_status,
        json=lambda: {"message": {"content": "oops"}},
    )
    mock_requests_post.return_value = mock_response

    client = ollama_ai.OllamaClient(
        api_url="http://localhost:11434/api/chat", model="test"
    )
    out = client._send_request([{"role": "user", "content": "test"}])  # pylint: disable=protected-access

    assert isinstance(out, dict)
    assert out["dialogue"] == "Error: LLM request failed with status 500."
    mock_requests_post.assert_called_once()


def test_ollama_client_send_request_chunked_response(mock_requests_post):
    """
    Tests that _send_request correctly processes a simulated chunked response.
    """
    mock_response = SimpleNamespace(
        content="part1part2part3",
        status_code=200,
        json=lambda: {"message": {"content": "part1part2part3"}},
        text="part1part2part3",
        raise_for_status=lambda: None,
    )
    mock_requests_post.return_value = mock_response

    client = ollama_ai.OllamaClient(
        api_url="http://localhost:11434/api/chat", model="test"
    )
    out = client._send_request([{"role": "user", "content": "test"}])  # pylint: disable=protected-access

    assert isinstance(out, dict)
    assert "part1part2part3" in out["dialogue"]
    mock_requests_post.assert_called_once()
