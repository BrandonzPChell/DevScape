import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from devscape.main import Game
from devscape.state import LLMCharacter, Player  # Import Player and LLMCharacter


@pytest.fixture
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
    llm_char = LLMCharacter(
        id="llm_1", name="LLM", x=0, y=0, art=[], mood="neutral", traits={}
    )
    mock_state_manager.get_game_state.return_value = MagicMock(
        player=Player(
            id="player_1", name="Player", x=0, y=0, art=[], health=100, max_health=100
        ),
        entities={"llm_1": llm_char},
        llm_character=llm_char,
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


def test_apply_planetary_event_storm_decreases_courage(game_instance):
    """
    Tests that a 'storm' event correctly decreases the LLM character's courage
    and updates mood and event log.
    """
    game_instance.llm_character_id = "llm_1"
    game_instance.state_manager.get_game_state().entities["llm_1"].traits = {
        "courage": 5
    }
    game_instance.state_manager.get_game_state().planetary_mood = 0.0  # Reset mood

    game_instance.apply_planetary_event("storm")

    assert (
        game_instance.state_manager.get_game_state().entities["llm_1"].traits["courage"]
        == 4
    )
    assert (
        game_instance.state_manager.get_game_state().entities["llm_1"].mood == "anxious"
    )
    assert game_instance.planetary_mood == -0.3
    assert len(game_instance.event_log) == 1
    assert game_instance.event_log[0]["event"] == "storm"


def test_apply_planetary_event_eclipse_increases_focus(game_instance):
    """
    Tests that an 'eclipse' event correctly increases the LLM character's focus
    and updates mood and event log.
    """
    game_instance.llm_character_id = "llm_1"
    game_instance.state_manager.get_game_state().entities["llm_1"].traits = {"focus": 2}
    game_instance.state_manager.get_game_state().planetary_mood = 0.0  # Reset mood

    game_instance.apply_planetary_event("eclipse")

    assert (
        game_instance.state_manager.get_game_state().entities["llm_1"].traits["focus"]
        == 3
    )
    assert game_instance.state_manager.get_game_state().entities["llm_1"].mood == "calm"
    assert game_instance.planetary_mood == 0.2
    assert len(game_instance.event_log) == 1
    assert game_instance.event_log[0]["event"] == "eclipse"


def test_apply_planetary_event_festival_increases_empathy(game_instance):
    """
    Tests that a 'festival' event correctly increases the LLM character's empathy
    and updates mood and event log.
    """
    game_instance.llm_character_id = "llm_1"
    game_instance.state_manager.get_game_state().entities["llm_1"].traits = {
        "empathy": 1
    }
    game_instance.state_manager.get_game_state().planetary_mood = 0.0  # Reset mood

    game_instance.apply_planetary_event("festival")

    assert (
        game_instance.state_manager.get_game_state().entities["llm_1"].traits["empathy"]
        == 2
    )
    assert (
        game_instance.state_manager.get_game_state().entities["llm_1"].mood == "joyful"
    )
    assert game_instance.planetary_mood == 0.7
    assert len(game_instance.event_log) == 1
    assert game_instance.event_log[0]["event"] == "festival"


def test_apply_planetary_event_unknown_event_resets_mood(game_instance):
    """
    Tests that an unknown event resets the LLM character's mood to neutral
    and logs the event without changing traits.
    """
    game_instance.llm_character_id = "llm_1"
    game_instance.state_manager.get_game_state().entities["llm_1"].traits = {
        "courage": 5
    }
    game_instance.state_manager.get_game_state().planetary_mood = (
        0.5  # Set a non-neutral mood
    )

    game_instance.apply_planetary_event("unknown_event")

    assert (
        game_instance.state_manager.get_game_state().entities["llm_1"].traits["courage"]
        == 5
    )  # Trait unchanged
    assert (
        game_instance.state_manager.get_game_state().entities["llm_1"].mood == "neutral"
    )
    assert game_instance.planetary_mood == 0.0
    assert len(game_instance.event_log) == 1
    assert game_instance.event_log[0]["event"] == "unknown_event"
