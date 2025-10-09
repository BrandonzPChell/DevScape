import pytest
from unittest.mock import patch
from game.main import Game, Entity

@pytest.fixture
def game_instance():
    """Fixture to create a Game instance with pygame dependencies mocked."""
    with patch('pygame.init'), patch('pygame.font.init'), patch('pygame.font.Font'):
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
    entity = Entity("test", 0, 0, [])

    # Test valid move
    entity.move(1, 0, game_map) # Move right
    assert (entity.x, entity.y) == (1, 0)

    # Test blocked move (into a wall)
    entity.x, entity.y = 1, 0
    entity.move(0, 1, game_map) # Move down into wall
    assert (entity.x, entity.y) == (1, 0) # Position should not change

    # Test diagonal move (should be prevented)
    entity.x, entity.y = 0, 0
    entity.move(1, 1, game_map)
    assert (entity.x, entity.y) == (0, 0) # Position should not change

    # Test out-of-bounds move
    entity.x, entity.y = 0, 0
    entity.move(-1, 0, game_map) # Move left off the map
    assert (entity.x, entity.y) == (0, 0) # Position should not change

def test_update_planetary_mood(game_instance):
    """Tests that update_planetary_mood correctly updates the mood and handles fallbacks."""
    # Test a valid mood
    game_instance.update_planetary_mood("joyful")
    assert game_instance.llm_character.mood == "joyful"
    assert game_instance.planetary_mood == 0.7

    # Test an unrecognized mood (should fallback to neutral)
    game_instance.update_planetary_mood("confused")
    assert game_instance.llm_character.mood == "neutral"
    assert game_instance.planetary_mood == 0.0

def test_apply_planetary_event(game_instance):
    """Tests that apply_planetary_event correctly modifies mood, traits, and logs."""
    game_instance.llm_character.traits = {"empathy": 0, "focus": 0}

    # Test "festival" event
    game_instance.apply_planetary_event("festival")
    assert game_instance.llm_character.mood == "joyful"
    assert game_instance.llm_character.traits["empathy"] == 1
    assert len(game_instance.event_log) == 1
    assert game_instance.event_log[0]["event"] == "festival"

    # Test "eclipse" event
    game_instance.apply_planetary_event("eclipse")
    assert game_instance.llm_character.mood == "calm"
    assert game_instance.llm_character.traits["focus"] == 1
    assert len(game_instance.event_log) == 2
    assert game_instance.event_log[1]["event"] == "eclipse"
