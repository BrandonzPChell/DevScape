"""Tests for the export functions in game.main."""

import json
from unittest.mock import patch

import pytest

from devscape.constants import ENTITY_TYPES
from devscape.main import Game
from devscape.state import LLMCharacter


@pytest.fixture
def game_instance():
    """Fixture to create a Game instance with pygame dependencies mocked."""
    with (
        patch("pygame.init"),
        patch("pygame.font.init"),
        patch("pygame.font.Font"),
        patch("pygame.time.get_ticks", return_value=12345),
    ):
        game = Game()
        # Manually assign llm_character from state_manager for testing purposes
        llm_char_found = None
        for entity in game.state_manager.get_game_state().entities.values():
            if (
                isinstance(entity, LLMCharacter)
                and entity.entity_type != ENTITY_TYPES["PLAYER"]
            ):
                llm_char_found = entity
                break
        game.llm_character = llm_char_found
        yield game


def test_export_data(game_instance):  # pylint: disable=W0621
    """Tests that export_data returns a valid JSON string with the correct structure."""
    game_instance.player.x = 10
    game_instance.player.y = 20
    game_instance.llm_character.mood = "happy"

    data_json = game_instance.export_data()
    data = json.loads(data_json)

    assert data["player"]["x"] == 10
    assert data["player"]["y"] == 20
    assert data["llm_character"]["mood"] == "happy"
    assert "timestamp" in data
    assert "version" in data


def test_export_timeline(game_instance):
    """Tests that export_timeline returns a JSON string of the timeline log."""
    game_instance.timeline_log = [
        {"timestamp": 1, "mood": "neutral", "traits": {}},
        {"timestamp": 2, "mood": "happy", "traits": {"patience": 1}},
    ]

    timeline_json = game_instance.export_timeline()
    data = json.loads(timeline_json)

    assert len(data) == 2
    assert data[1]["mood"] == "happy"
    assert data[1]["traits"]["patience"] == 1


def test_export_trait_chart(game_instance):
    """Tests that export_trait_chart returns a JSON string with trait data."""
    game_instance.llm_character.traits = {"patience": 5, "courage": 2}
    game_instance.timeline_log = [{"timestamp": 1}, {"timestamp": 2}, {"timestamp": 3}]

    chart_json = game_instance.export_trait_chart()
    data = json.loads(chart_json)

    assert data["traits"]["patience"] == 5
    assert data["traits"]["courage"] == 2
    assert data["history_length"] == 3
    assert data["timestamp"] == 3


def test_export_constellation(game_instance):
    """Tests that export_constellation returns a JSON string with event and glyph data."""
    game_instance.event_log = [
        {"event": "storm", "mood": "anxious"},
        {"event": "festival", "mood": "joyful"},
    ]

    constellation_json = game_instance.export_constellation()
    data = json.loads(constellation_json)

    assert len(data["events"]) == 2
    assert data["events"][0]["event"] == "storm"
    assert len(data["glyphs"]) == 2
    assert data["glyphs"][0] == "⚡"
    assert data["glyphs"][1] == "☀"
    assert "lineage" in data
