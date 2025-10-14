# tests/test_main_minimal.py
import importlib
import sys
import types

import devscape.main as gm  # Moved to top-level
from devscape import ollama_ai as ollama_ai_mod


def test_module_constants():
    # import devscape.main as gm # Removed

    assert hasattr(gm, "__version__")
    assert isinstance(gm.__version__, str)
    assert gm.BLACK == (0, 0, 0)
    assert gm.WHITE == (255, 255, 255)


def test_game_can_be_instantiated_with_stubbed_dependencies(monkeypatch):
    # Create a mock pygame module
    mock_pygame = types.SimpleNamespace()
    mock_pygame.init = lambda *a, **k: None
    mock_pygame.font = types.SimpleNamespace(
        init=lambda *a, **k: None,
        Font=lambda *a, **k: types.SimpleNamespace(render=lambda *a, **k: None),
    )
    mock_pygame.display = types.SimpleNamespace(
        set_mode=lambda *a, **k: types.SimpleNamespace(),
        set_caption=lambda *a, **k: None,
    )
    mock_pygame.time = types.SimpleNamespace(
        Clock=lambda *a, **k: types.SimpleNamespace(tick=lambda x: 0)
    )
    mock_pygame.event = types.SimpleNamespace(
        get=lambda *a, **k: []
    )  # Mock event.get for Game.run() if it's called

    # Replace the real pygame module with our mock in sys.modules
    # This ensures that when game.main imports pygame, it gets our mock.
    monkeypatch.setitem(sys.modules, "pygame", mock_pygame)

    mod = importlib.import_module("devscape.main")

    # stub heavy dependencies used by Game
    game_state = types.SimpleNamespace(
        player="player-stub",
        llm_character="llm-stub",
        entities={"llm-stub": "llm-stub"},
    )
    monkeypatch.setattr(
        mod,
        "StateManager",
        lambda *a, **k: types.SimpleNamespace(
            game_state=game_state,
            get_game_state=lambda: game_state,
        ),
    )
    monkeypatch.setattr(
        ollama_ai_mod, "OllamaClient", lambda *a, **k: "ollama-client-stub"
    )
    monkeypatch.setattr(mod, "draw_chat_bubble", lambda *a, **k: None)
    monkeypatch.setattr(mod, "render_dashboard_content", lambda *a, **k: None)
    monkeypatch.setattr(mod, "render_pixel_art", lambda *a, **k: None)

    # instantiate Game
    game_instance = mod.Game()
    assert isinstance(game_instance, mod.Game)
    assert hasattr(game_instance, "__class__")
    assert getattr(mod, "__version__", "").startswith("0")
