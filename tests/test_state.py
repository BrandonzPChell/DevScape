"""Tests for the game state management (Entity)."""

import json
from unittest.mock import patch

import pytest

from devscape.main import Game
from devscape.state import Entity


@pytest.fixture
def game_instance():
    """Fixture to create a Game instance with pygame dependencies mocked."""
    with patch("pygame.init"), patch("pygame.font.init"), patch("pygame.font.Font"):
        game = Game()
        yield game


# --- Tier 3 Tests: State-Modifying Methods ---


def test_entity_move():
    """Tests the Entity.move method for valid, blocked, and invalid moves."""
    game_map = [
        "GGGGG",
        "GWWWG",
        "GWGWG",
        "GWWWG",
        "GGGGG",
    ]
    # Start at a non-trapped position
    entity = Entity("test", "test_entity", 0, 0, [])  # Added name and art

    # Test valid move
    entity.move(1, 0, game_map)  # Move right
    assert (entity.x, entity.y) == (1, 0)

    # Test blocked move (into a wall)
    entity.x, entity.y = 1, 0
    entity.move(0, 1, game_map)  # Move down into wall
    assert (entity.x, entity.y) == (1, 0)  # Position should not change

    # Test diagonal move (should be prevented)
    entity.x, entity.y = 0, 0
    entity.move(1, 1, game_map)
    assert (entity.x, entity.y) == (0, 0)  # Position should not change

    # Test out-of-bounds move
    entity.x, entity.y = 0, 0
    entity.move(-1, 0, game_map)  # Move left off the map
    assert (entity.x, entity.y) == (0, 0)  # Position should not change


def test_update_planetary_mood(game_instance):
    """Tests that update_planetary_mood correctly updates the mood and handles fallbacks."""
    # Test a valid mood
    game_instance.update_planetary_mood("joyful")
    assert (
        game_instance.state_manager.get_game_state()
        .entities.get(game_instance.llm_character_id)
        .mood
        == "joyful"
    )
    assert game_instance.planetary_mood == 0.7

    # Test an unrecognized mood (should fallback to neutral)
    game_instance.update_planetary_mood("confused")
    assert (
        game_instance.state_manager.get_game_state()
        .entities.get(game_instance.llm_character_id)
        .mood
        == "neutral"
    )
    assert game_instance.planetary_mood == 0.0


def test_apply_planetary_event(game_instance):
    """Tests that apply_planetary_event correctly modifies mood, traits, and logs."""
    game_instance.state_manager.get_game_state().entities.get(
        game_instance.llm_character_id
    ).traits = {"empathy": 0, "focus": 0}

    # Test "festival" event
    game_instance.apply_planetary_event("festival")
    assert (
        game_instance.state_manager.get_game_state()
        .entities.get(game_instance.llm_character_id)
        .mood
        == "joyful"
    )
    assert (
        game_instance.state_manager.get_game_state()
        .entities.get(game_instance.llm_character_id)
        .traits["empathy"]
        == 1
    )
    assert len(game_instance.event_log) == 1
    assert game_instance.event_log[0]["event"] == "festival"

    # Test "eclipse" event
    game_instance.apply_planetary_event("eclipse")
    assert (
        game_instance.state_manager.get_game_state()
        .entities.get(game_instance.llm_character_id)
        .mood
        == "calm"
    )
    assert (
        game_instance.state_manager.get_game_state()
        .entities.get(game_instance.llm_character_id)
        .traits["focus"]
        == 1
    )
    assert len(game_instance.event_log) == 2
    assert game_instance.event_log[1]["event"] == "eclipse"


# -------------------------------------------------------------------
# Phase 28a: Edge Guardians (Menu Edge Cases)
# -------------------------------------------------------------------

# def test_menu_edge_cases(monkeypatch):
#     """Ensure menu handles empty options and invalid selections gracefully."""
#     from game.main import menu  # adjust if menu lives elsewhere
#
#     # Case 1: Empty options
#     monkeypatch.setattr("builtins.input", lambda _: "0")  # simulate any input
#     result = menu("Choose wisely:", [])
#     # Should return None or safe fallback, not crash
#     # assert result is None or result == ""
#
#     # Case 2: Invalid selection (out of range)
#     inputs = iter(["99", "1"])  # first invalid, then valid
#     monkeypatch.setattr("builtins.input", lambda _: next(inputs))
#     result = menu("Pick an option:", ["apple", "banana"])
#     # Should eventually return a valid choice
#     # assert result in ["apple", "banana"]

# -------------------------------------------------------------------
# Phase 28b: Stress Guardians (Sprite Edge Cases)
# -------------------------------------------------------------------


def test_generate_sprite_edge_cases(game_instance):
    """Ensure generate_sprite handles empty and very long seeds safely."""
    g = game_instance

    # Case 1: Empty seed
    sprite_empty = g.generate_sprite("")
    assert isinstance(sprite_empty, list)
    assert all(isinstance(row, str) for row in sprite_empty)
    assert len(sprite_empty) > 0

    # Case 2: Very long seed
    long_seed = "x" * 1000
    sprite_long = g.generate_sprite(long_seed)
    assert isinstance(sprite_long, list)
    assert all(isinstance(row, str) for row in sprite_long)
    assert len(sprite_long) > 0

    # Case 3: Consistency check
    row_lengths = {len(row) for row in sprite_long}
    assert len(row_lengths) == 1  # all rows equal length


# -------------------------------------------------------------------
# Phase 28d: Regression Guardians (Final Export Covenant)
# -------------------------------------------------------------------


def test_export_functions_consistency(game_instance):
    """Ensure export_events and export_data always return consistent structures."""
    # Clear logs and traits
    game_instance.timeline_log = []
    game_instance.event_log = []
    game_instance.state_manager.get_game_state().entities.get(
        game_instance.llm_character_id
    ).traits = {}
    # Case 1: export_events always returns a list
    events_json = game_instance.export_events()
    events = json.loads(events_json)  # Parse the JSON string
    assert isinstance(events, list)
    assert events == []

    # Case 2: export_data always includes top-level keys
    exported_str = game_instance.export_data()
    exported = json.loads(exported_str)

    for key in ["timeline_log", "event_log", "traits", "timestamp", "version"]:
        assert key in exported
