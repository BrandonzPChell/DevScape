# tests/test_ollama_ai_unit.py


from types import SimpleNamespace

from src.devscape import ollama_ai


class DummySuccess:
    def __init__(self, text):
        self.text = text
        self.status_code = 200


class DummyError:
    def __init__(self):
        self.text = "error"
        self.status_code = 500


def test_send_request_returns_payload_on_success(monkeypatch):
    def mock_post(*args, **kwargs):
        mock_response = SimpleNamespace()
        mock_response.status_code = 200
        mock_response.json = lambda: {"message": {"content": "hello from AI"}}
        mock_response.text = (
            '{"message": {"content": "hello from AI"}}'  # Added text attribute
        )
        mock_response.raise_for_status = lambda: None
        return mock_response

    monkeypatch.setattr(ollama_ai.requests, "post", mock_post)

    client = ollama_ai.OllamaClient(api_url="http://fake-url", model="fake-model")
    messages = [{"role": "user", "content": "a prompt"}]
    out = client._send_request(messages)
    assert out == {"move": None, "dialogue": "hello from AI", "raw": "hello from AI"}


def test_send_request_raises_on_client_error(monkeypatch):
    def mock_post(*args, **kwargs):
        raise ollama_ai.requests.exceptions.RequestException("transport failure")

    monkeypatch.setattr(ollama_ai.requests, "post", mock_post)

    client = ollama_ai.OllamaClient(api_url="http://fake-url", model="fake-model")
    messages = [{"role": "user", "content": "a prompt"}]
    out = client._send_request(messages)
    assert out == {"move": None, "dialogue": "I feel disconnected...", "raw": ""}
