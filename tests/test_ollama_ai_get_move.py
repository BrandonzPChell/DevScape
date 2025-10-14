import pytest


def make_get_move_and_dialogue_mock(rv=None, exc=None):
    def _mock_method(*_args, **_kwargs):
        if exc:
            raise exc
        return rv

    return _mock_method


def test_get_llm_move_success(monkeypatch):
    mod = pytest.importorskip("game.ollama_ai")
    if not hasattr(mod, "get_llm_move"):
        pytest.skip("get_llm_move not present in game.ollama_ai")

    # Mock the internal ollama_client.get_move_and_dialogue method
    mock_return_value = (
        (0, 1),
        "move: north",
    )  # Example return: (move_delta, dialogue)
    monkeypatch.setattr(
        mod.ollama_client,
        "get_move_and_dialogue",
        make_get_move_and_dialogue_mock(rv=mock_return_value),
    )

    # Call the module-level get_llm_move with dummy arguments
    move_delta, dialogue = mod.get_llm_move(0, 0, 0, 0, [], "neutral")

    assert move_delta == (0, 1)
    assert dialogue == "move: north"


def test_get_llm_move_handles_transport_error(monkeypatch):
    mod = pytest.importorskip("game.ollama_ai")
    if not hasattr(mod, "get_llm_move"):
        pytest.skip("get_llm_move not present in game.ollama_ai")

    # Mock the internal ollama_client.get_move_and_dialogue method to raise an exception
    monkeypatch.setattr(
        mod.ollama_client,
        "get_move_and_dialogue",
        make_get_move_and_dialogue_mock(exc=RuntimeError("boom")),
    )

    # Call the module-level get_llm_move with dummy arguments
    with pytest.raises(RuntimeError):
        mod.get_llm_move(0, 0, 0, 0, [], "neutral")
