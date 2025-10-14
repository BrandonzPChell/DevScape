from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from devscape.main import Game
from devscape.state import LLMCharacter, Player


@pytest.fixture(autouse=True)
def mock_game_dependencies(monkeypatch):
    """Mocks pygame and other heavy dependencies for Game instantiation."""
    mock_pygame = SimpleNamespace(
        init=lambda *a, **k: None,
        font=SimpleNamespace(
            init=lambda *a, **k: None,
            Font=lambda *a, **k: SimpleNamespace(render=lambda *a, **k: MagicMock()),
        ),
        display=SimpleNamespace(
            set_mode=lambda *a, **k: SimpleNamespace(), set_caption=lambda *a, **k: None
        ),
        time=SimpleNamespace(
            Clock=lambda *a, **k: SimpleNamespace(tick=lambda x: 0), get_ticks=lambda: 0
        ),
        event=SimpleNamespace(get=lambda *a, **k: []),
    )
    monkeypatch.setattr("devscape.main.pygame", mock_pygame)

    # Mock StateManager and its internal components
    mock_state_manager = MagicMock()
    mock_state_manager.get_game_state.return_value = MagicMock(
        player=Player(
            id="player_1", name="Player", x=0, y=0, art=[], health=100, max_health=100
        ),
        llm_character=LLMCharacter(
            id="llm_1", name="LLM", x=0, y=0, art=[], mood="neutral", traits={}
        ),
        event_log=[],
        planetary_mood=0.0,
    )
    mock_state_manager._new_game.return_value = (  # pylint: disable=protected-access
        mock_state_manager.get_game_state.return_value
    )
    monkeypatch.setattr(
        "devscape.state_manager.StateManager",
        MagicMock(return_value=mock_state_manager),
    )

    # Mock OllamaClient
    monkeypatch.setattr("devscape.ollama_ai.OllamaClient", MagicMock())

    # Mock rendering functions
    monkeypatch.setattr("devscape.main.draw_chat_bubble", lambda *a, **k: None)
    monkeypatch.setattr("devscape.main.render_dashboard_content", lambda *a, **k: None)
    monkeypatch.setattr("devscape.main.render_pixel_art", lambda *a, **k: None)

    return mock_state_manager


@pytest.fixture
def game_instance(mock_game_dependencies):
    """Provides a Game instance with mocked dependencies for each test."""
    game = Game()
    game.state_manager = mock_game_dependencies  # Assign the mocked state_manager
    return game


def test_generate_overlay_happy_mood(game_instance):
    """
    Tests that generate_overlay produces a happy overlay.
    """
    overlay = game_instance.generate_overlay("happy")
    assert isinstance(overlay, list)
    assert all(isinstance(line, str) for line in overlay)
    assert len(overlay) > 0
    joined = "\n".join(overlay).lower()
    assert any(tok in joined for tok in ("happy", "joy", "o", "yay", "\\", "/"))


def test_generate_overlay_neutral_mood(game_instance):
    """
    Tests that generate_overlay produces a neutral overlay.
    """
    overlay = game_instance.generate_overlay("neutral")
    assert isinstance(overlay, list)
    assert all(isinstance(line, str) for line in overlay)
    assert len(overlay) > 0
    # neutral overlay should not be identical to happy overlay
    assert overlay != game_instance.generate_overlay("happy")


def test_generate_overlay_unknown_mood_defaults_to_neutral(game_instance):
    """
    Tests that generate_overlay defaults to a neutral overlay for unknown moods.
    """
    overlay = game_instance.generate_overlay("unknown_mood")
    neutral_overlay = game_instance.generate_overlay("neutral")
    assert overlay == neutral_overlay
