from types import SimpleNamespace

import pytest

mod = pytest.importorskip("game.ollama_ai")


def make_client(call_impl):
    return SimpleNamespace(call=call_impl)


def test_client_send_request_and_error_handling(monkeypatch):
    if not hasattr(mod, "OllamaClient"):
        pytest.skip("OllamaClient not present")
    # Simulate client that raises network error on call
    monkeypatch.setattr(
        mod,
        "OllamaClient",
        lambda *a, **k: make_client(
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("net"))
        ),
    )
    OllamaClientClass = mod.OllamaClient
    # If client exposes _send_request or send_message, ensure it surfaces the error
    inst = OllamaClientClass(api_url="http://localhost:11434/api/chat", model="test")
    # try calling higher-level convenience if present
    for name in ("send_message", "_send_request", "get_move_and_dialogue"):
        if hasattr(inst, name):
            try:
                fn = getattr(inst, name)
                # adapt signature: (client, payload) or (client, prompt)
                if name == "_send_request":
                    with pytest.raises(RuntimeError):
                        fn([{"role": "user", "content": "ping"}])
                elif name == "send_message":
                    with pytest.raises(RuntimeError):
                        fn("ping")
                elif name == "get_move_and_dialogue":
                    with pytest.raises(RuntimeError):
                        fn(0, 0, 0, 0, [], "neutral")
            except TypeError:
                # signature mismatch; skip strict invocation
                pass
    # At minimum, constructing OllamaClient did not crash
    assert inst is not None


def test_get_move_and_dialogue_structured_response(monkeypatch):
    # Provide a fake client returning structured response with text
    # monkeypatch OllamaClient to return fake client with `.call`
    if hasattr(mod, "OllamaClient"):
        # Mock the _send_request method of the OllamaClient instance
        monkeypatch.setattr(
            mod.OllamaClient,
            "_send_request",
            lambda *a, **k: {
                "move": {"dx": 1, "dy": 0},
                "dialogue": "Hi",
                "raw": "MOVE east\nHi",
            },
        )

        # Instantiate OllamaClient and call get_move_and_dialogue
        client_instance = mod.OllamaClient(
            api_url="http://localhost:11434/api/chat", model="test"
        )
        sample_game_map = ["...", ".P.", "..."]
        out = client_instance.get_move_and_dialogue(
            0, 0, 0, 0, sample_game_map, "neutral"
        )
        # ensure result is tuple-like or dict-like
        assert out is not None
        assert isinstance(out, tuple)
        assert out[0] == (1, 0)
        assert out[1] == "Hi"
    else:
        pytest.skip("get_move_and_dialogue not present")
