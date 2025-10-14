import sys
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
    monkeypatch.setitem(sys.modules, "pygame", mock_pygame)

    # Mock StateManager and its internal components
    mock_state_manager = MagicMock()
    player = Player(
        id="player_1", name="Player", x=0, y=0, art=[], health=100, max_health=100
    )
    player.entity_type = "PLAYER"
    llm_char = LLMCharacter(
        id="llm_1", name="LLM", x=0, y=0, art=[], mood="neutral", traits={}
    )
    llm_char.entity_type = "LLM_CHARACTER"
    mock_state_manager.get_game_state.return_value = MagicMock(
        player=player,
        llm_character=llm_char,
        entities={"player_1": player, "llm_1": llm_char},
        event_log=[],
        planetary_mood=0.0,
    )
    mock_state_manager.get_all_entities.return_value = {
        "player_1": player,
        "llm_1": llm_char,
    }
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
    game.player = mock_game_dependencies.get_game_state().player
    return game


def test_generate_overlay_variants(game_instance):
    """
    Tests that generate_overlay produces expected output for different moods.
    """
    happy = game_instance.generate_overlay("happy")
    neutral = game_instance.generate_overlay("neutral")
    sad = game_instance.generate_overlay("sad")

    assert isinstance(happy, list) and all(isinstance(x, str) for x in happy)
    assert isinstance(neutral, list) and all(isinstance(x, str) for x in neutral)
    assert isinstance(sad, list) and all(isinstance(x, str) for x in sad)
    assert happy != neutral or neutral != sad  # Ensure they are not all the same


def test_render_helper_invoked(game_instance, monkeypatch):
    """
    Tests that a rendering helper function is invoked.
    """
    calls = {}

    def fake_draw(*a, **k):
        calls["draw"] = calls.get("draw", 0) + 1

    monkeypatch.setattr("devscape.main.draw_chat_bubble", fake_draw)

    game_instance.show_chat_bubble(game_instance.player, "hello")
    game_instance.render()

    assert calls["draw"] >= 1
