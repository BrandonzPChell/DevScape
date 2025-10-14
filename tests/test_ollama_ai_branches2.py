from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import requests


def mock_requests_post(mock_response):
    def _mock_post(*_args, **_kwargs):
        return mock_response

    return _mock_post


def test_request_text_various_shapes(monkeypatch):
    mod = pytest.importorskip("devscape.ollama_ai")

    # bytes content
    resp1 = SimpleNamespace(
        content=b"hi bytes",
        status_code=200,
        json=lambda: {"message": {"content": "hi bytes"}},
        text="hi bytes",
        raise_for_status=lambda: None,
    )
    monkeypatch.setattr(requests, "post", mock_requests_post(resp1))
    client1 = mod.OllamaClient(api_url="http://localhost:11434/api/chat", model="test")
    out1 = client1._send_request(
        [{"role": "user", "content": "test"}]
    )  # pylint: disable=protected-access
    assert isinstance(out1, dict) and "hi bytes" in out1["dialogue"]

    # object with no .text but .content as str
    resp2 = SimpleNamespace(
        content="plain",
        status_code=200,
        json=lambda: {"message": {"content": "plain"}},
        text="plain",
        raise_for_status=lambda: None,
    )
    monkeypatch.setattr(requests, "post", mock_requests_post(resp2))
    client2 = mod.OllamaClient(api_url="http://localhost:11434/api/chat", model="test")
    out2 = client2._send_request(
        [{"role": "user", "content": "test"}]
    )  # pylint: disable=protected-access
    assert isinstance(out2, dict) and "plain" in out2["dialogue"]

    # iterable / streaming response (simulated as a single response for _send_request)
    resp3 = SimpleNamespace(
        content="ab",
        status_code=200,
        json=lambda: {"message": {"content": "ab"}},
        text="ab",
        raise_for_status=lambda: None,
    )
    monkeypatch.setattr(requests, "post", mock_requests_post(resp3))
    client3 = mod.OllamaClient(api_url="http://localhost:11434/api/chat", model="test")
    out3 = client3._send_request(
        [{"role": "user", "content": "test"}]
    )  # pylint: disable=protected-access
    assert isinstance(out3, dict) and "ab" in out3["dialogue"]

    # non-200 -> expect error handling (returns fallback message)
    def mock_raise_for_status():
        raise requests.exceptions.HTTPError("500 Server Error")

    resp4 = SimpleNamespace(
        text="err",
        status_code=500,
        raise_for_status=mock_raise_for_status,
        json=lambda: {"message": {"content": "err"}},
    )
    monkeypatch.setattr(requests, "post", mock_requests_post(resp4))
    client4 = mod.OllamaClient(api_url="http://localhost:11434/api/chat", model="test")
    out4 = client4._send_request(
        [{"role": "user", "content": "test"}]
    )  # pylint: disable=protected-access
    assert (
        isinstance(out4, dict)
        and "Error: LLM request failed with status 500." in out4["dialogue"]
    )


def test_get_llm_move_transport_error(monkeypatch):
    mod = pytest.importorskip("devscape.ollama_ai")
    if not hasattr(mod, "get_llm_move"):
        pytest.skip("get_llm_move missing")

    # Mock the internal ollama_client.get_move_and_dialogue method to raise an exception
    monkeypatch.setattr(mod, "ollama_client", MagicMock())
    monkeypatch.setattr(
        mod.ollama_client,
        "get_move_and_dialogue",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    # Call the module-level get_llm_move with dummy arguments
    with pytest.raises(RuntimeError):
        mod.get_llm_move(0, 0, 0, 0, [], "neutral")
