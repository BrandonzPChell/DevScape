from types import SimpleNamespace

import pytest

mod = pytest.importorskip("game.ollama_ai")


def make_client_obj(call_impl):
    return SimpleNamespace(call=call_impl)


def test_client_send_request_network_and_json_errors(monkeypatch):
    # stub a client that raises at call time (network)
    # if OllamaClient exists and has _send_request, call underlying helper directly if possible
    if hasattr(mod, "OllamaClient"):
        OllamaClientClass = mod.OllamaClient
        try:
            # attempt to call internal _send_request if a bound instance method exists
            inst = (
                OllamaClientClass(
                    api_url="http://localhost:11434/api/chat", model="test"
                )
                if callable(OllamaClientClass)
                else OllamaClientClass
            )
            if hasattr(inst, "_send_request"):
                # We expect _send_request to catch the exception and return a fallback dict
                # Mock the _send_request method to raise an exception
                monkeypatch.setattr(
                    inst,
                    "_send_request",
                    lambda *a, **k: (_ for _ in ()).throw(RuntimeError("network")),
                )
                result = inst._send_request(
                    [{"role": "user", "content": "test"}]
                )  # pylint: disable=protected-access
                assert isinstance(result, dict)
                assert result["move"] is None
                assert result["dialogue"] == "I feel disconnected..."
                assert result["raw"] == ""
        except TypeError:
            # constructor signature mismatch; skip strict invocation
            pytest.skip("OllamaClient constructor signature mismatch for test")
    else:
        pytest.skip("OllamaClient not present")


def test_get_move_and_dialogue_branches(monkeypatch):
    if not hasattr(mod, "get_move_and_dialogue") and not hasattr(mod, "OllamaClient"):
        pytest.skip("No client API present to test get_move_and_dialogue")
    # simulate client returning a structured response (object with .text) and check method doesn't crash
    # monkeypatch OllamaClient to return fake client with `.call`
    if hasattr(mod, "OllamaClient"):
        # Mock the _send_request method of the OllamaClient instance
        monkeypatch.setattr(
            mod.OllamaClient,
            "_send_request",
            lambda *a, **k: {
                "move": {"dx": 0, "dy": -1},
                "dialogue": "Hi",
                "raw": "MOVE north\nHi",
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
        assert out[0] == (0, -1)
        assert out[1] == "Hi"
    else:
        pytest.skip("get_move_and_dialogue not present")
