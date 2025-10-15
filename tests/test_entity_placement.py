import pytest
import random

from devscape.entity_manager import place_initial_entities
from devscape.state import Map, LLMCharacter

@pytest.fixture
def mock_game_map():
    game_map = Map(10, 10)
    game_map.generate_map()
    return game_map

@pytest.fixture
def mock_player_position():
    return (5, 5)

def test_place_initial_entities_no_overlap_and_within_bounds(mock_game_map, mock_player_position):
    # Mock random to make entity placement deterministic for testing
    random.seed(42)

    entities = {}
    place_initial_entities(mock_game_map, entities, mock_player_position)

    # Assert no entity is at the player's initial position
    for entity_id, entity in entities.items():
        assert (entity.x, entity.y) != mock_player_position

    # Assert all entities are within map bounds
    for entity_id, entity in entities.items():
        assert 0 <= entity.x < mock_game_map.width
        assert 0 <= entity.y < mock_game_map.height

    # Assert the correct number of enemies and NPCs are placed (within the random range)
    enemy_count = sum(1 for e in entities.values() if isinstance(e, LLMCharacter) and "enemy" in e.id)
    npc_count = sum(1 for e in entities.values() if isinstance(e, LLMCharacter) and "npc" in e.id)

    # Based on random.seed(42), the expected counts are 3 enemies and 1 NPC
    assert enemy_count == 3
    assert npc_count == 1

    # Assert that entities are added to the game_map tiles
    for entity_id, entity in entities.items():
        tile = mock_game_map.tiles[entity.y][entity.x]
        assert entity_id in tile.entities
