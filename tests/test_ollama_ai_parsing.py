# tests/test_ollama_ai_parsing.py
from devscape import ollama_ai


# Mock the requests library's post method
class MockResponse:
    def __init__(self, json_data, status_code, text_data=None):
        self._json_data = json_data
        self.status_code = status_code
        self._text_data = text_data

    def json(self):
        return self._json_data

    @property
    def text(self):
        return self._text_data if self._text_data is not None else str(self._json_data)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise ollama_ai.requests.exceptions.HTTPError(
                f"HTTP Error: {self.status_code}"
            )


def mock_requests_post(_url, json, _timeout):
    # This mock needs to be more dynamic to handle different test cases
    # For now, let's assume a successful response
    if "error" in json.get("messages", [{}])[-1].get("content", ""):
        return MockResponse({"message": {"content": "error response"}}, 500)
    return MockResponse({"message": {"content": "hello from AI"}}, 200)


def test_send_request_success_json_content(monkeypatch):
    monkeypatch.setattr(
        ollama_ai.requests,
        "post",
        lambda url, json, timeout: MockResponse(
            {"message": {"content": "hello from AI"}},
            200,
            text_data='{"message": {"content": "hello from AI"}}',
        ),
    )
    client = ollama_ai.OllamaClient(api_url="http://fake-url", model="fake-model")
    messages = [{"role": "user", "content": "a prompt"}]
    out = client._send_request(messages)  # pylint: disable=protected-access


def test_send_request_success_text_content(monkeypatch):
    # Test case where response.json() fails, and response.text is used
    def mock_post_text_fallback(_url, json, timeout):
        mock_resp = MockResponse(None, 200, text_data="plain text response")
        mock_resp.json = lambda: (_ for _ in ()).throw(
            ValueError("Invalid JSON")
        )  # Simulate JSONDecodeError
        return mock_resp

    monkeypatch.setattr(ollama_ai.requests, "post", mock_post_text_fallback)
    client = ollama_ai.OllamaClient(api_url="http://fake-url", model="fake-model")
    messages = [{"role": "user", "content": "a prompt"}]
    out = client._send_request(messages)  # pylint: disable=protected-access
    assert out == {
        "move": None,
        "dialogue": "plain text response",
        "raw": "plain text response",
    }


def test_send_request_non200_status_error_handling(monkeypatch):
    monkeypatch.setattr(
        ollama_ai.requests,
        "post",
        lambda url, json, timeout: MockResponse({"error": "server error"}, 500),
    )
    client = ollama_ai.OllamaClient(api_url="http://fake-url", model="fake-model")
    messages = [{"role": "user", "content": "a prompt"}]
    out = client._send_request(messages)  # pylint: disable=protected-access
    assert out == {
        "move": {"dx": 0, "dy": 0},
        "dialogue": "Error: LLM request failed with status 500.",
        "raw": "",
    }


def test_send_request_transport_error_handling(monkeypatch):
    def mock_post_exception(url, json, timeout):
        raise ollama_ai.requests.exceptions.RequestException("transport failure")

    monkeypatch.setattr(ollama_ai.requests, "post", mock_post_exception)
    client = ollama_ai.OllamaClient(api_url="http://fake-url", model="fake-model")
    messages = [{"role": "user", "content": "a prompt"}]
    out = client._send_request(messages)  # pylint: disable=protected-access
    assert out == {"move": None, "dialogue": "I feel disconnected...", "raw": ""}
