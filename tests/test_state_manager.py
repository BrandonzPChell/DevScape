import random
from unittest.mock import patch

import pytest

from devscape.constants import ENTITY_TYPES  # Import ENTITY_TYPES
from devscape.state import Entity, GameState, Item, LLMCharacter, Player
from devscape.state_manager import StateManager


@pytest.fixture
def state_manager():
    """Fixture to create a StateManager instance for testing."""
    # Use a temporary file for saving/loading that will be cleaned up
    with (
        patch("devscape.state_manager.open", create=True),
        patch("os.path.exists", return_value=False),
    ):  # Changed to False for new game init
        manager = StateManager()
        return manager


@pytest.fixture
def mock_player():
    """Fixture to create a mock Player."""
    return Player(
        id="player_1",
        name="Test Player",
        x=5,
        y=5,
        art=[],
        health=100,
        max_health=100,
        xp=0,
        level=1,
    )


@pytest.fixture
def mock_item():
    """Fixture to create a mock Item."""
    return Item(
        id="item_1", name="Test Potion", description="A test item.", effect={"heal": 20}
    )


@pytest.fixture
def mock_enemy():
    """Fixture to create a mock enemy LLMCharacter."""
    return LLMCharacter(
        id="enemy_1",
        name="Test Goblin",
        x=6,
        y=5,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        health=50,
        max_health=50,
    )


def test_new_game_initializes_player_and_llm(state_manager):
    """
    Tests that a new game is initialized with a valid GameState,
    containing a player, entities, a map, and quests.
    """
    gs = state_manager.get_game_state()
    player = gs.player  # Access player from game_state
    # LLMCharacter is not directly accessible via get_llm_character() in StateManager
    # We need to find an LLMCharacter from the entities list
    llm_character = None
    for entity_id, entity in gs.entities.items():
        if (
            isinstance(entity, LLMCharacter)
            and entity.entity_type == ENTITY_TYPES["NPC"]
        ):
            llm_character = entity
            break
    if llm_character is None:
        for entity_id, entity in gs.entities.items():
            if (
                isinstance(entity, LLMCharacter)
                and entity.entity_type == ENTITY_TYPES["ENEMY"]
            ):
                llm_character = entity
                break

    assert isinstance(gs, GameState)
    assert isinstance(player, Player)
    assert llm_character is not None  # Ensure an LLMCharacter (NPC or Enemy) is found
    assert player.health == player.max_health
    assert llm_character.health == llm_character.max_health


def test_move_player_updates_position(state_manager):
    """
    Tests moving the player to a valid adjacent tile.
    Asserts that the player's position is updated and game turn increments.
    """
    player = state_manager.get_game_state().player
    old_pos = player.position

    # Ensure the new position is within bounds and not a wall
    # Assuming a default map, (x+1, y) should be valid for initial player position (0,0)
    # Need to ensure the map is large enough and the tile is not a wall

    state_manager.player_manager.move_player(1, 0)  # Move right
    new_pos = state_manager.get_game_state().player.position

    assert new_pos == (old_pos[0] + 1, old_pos[1])
    assert state_manager.get_current_turn() == 1


def test_add_and_remove_entity(state_manager):
    """
    Tests adding and removing an entity from the game state.
    """
    entity = Entity(
        id="test_entity",
        name="Test Entity",
        x=0,
        y=0,
        art=[],
        entity_type="GENERIC",
        color=(0, 0, 0),
    )
    state_manager.game_state.entities[entity.id] = entity
    state_manager.game_state.game_map.tiles[entity.y][entity.x].entities.append(
        entity.id
    )
    all_entities = state_manager.get_all_entities()
    assert "test_entity" in all_entities

    # To remove an entity, we need to remove it from the entities dict
    # and also from the tile it occupies.
    # The StateManager doesn't have a direct remove_entity method,
    # so we'll simulate the effect of an entity being defeated.
    del state_manager.game_state.entities[entity.id]
    state_manager.game_state.game_map.tiles[entity.y][entity.x].entities.remove(
        entity.id
    )

    assert "test_entity" not in state_manager.get_all_entities()


def test_pickup_item_adds_to_inventory(state_manager):
    """
    Tests that the player can pick up an item, and it is added to their inventory.
    """
    player = state_manager.get_game_state().player
    item = Item(
        id="gold_coin",
        name="Gold Coin",
        description="A shiny coin.",
        effect={"gold": 10},
    )

    initial_gold = player.inventory.gold
    initial_inventory_size = len(player.inventory.items)

    # Simulate picking up the item
    state_manager.player_manager.pickup_item(player, item)

    assert len(player.inventory.items) == initial_inventory_size + 1
    assert player.inventory.get_item("gold_coin") is not None
    assert player.inventory.gold == initial_gold + 10  # Gold should be added
    assert "You picked up a Gold Coin" in state_manager.get_game_messages()


def test_attack_entity_reduces_health(state_manager):
    """
    Tests a successful attack on an enemy within attack range.
    Asserts that the enemy's health is reduced.
    """
    player = state_manager.get_game_state().player
    # Place player and enemy close for attack
    player.position = (5, 5)
    enemy = LLMCharacter(
        id="enemy1",
        name="Test Goblin",
        x=6,
        y=5,  # Adjacent to player
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        health=50,
        max_health=50,
        xp=0,
        level=1,
        dialogue="",
        mood="neutral",
        traits={},
        sight_range=5,
    )
    state_manager.game_state.entities[enemy.id] = enemy
    state_manager.game_state.game_map.tiles[enemy.y][enemy.x].entities.append(enemy.id)

    initial_enemy_health = enemy.health

    state_manager.attack_entity("enemy1")

    assert enemy.health < initial_enemy_health
    assert "You attacked Test Goblin" in state_manager.get_game_messages()
    assert state_manager.get_current_turn() > 0

    def test_save_and_load_game_roundtrip(tmp_path):
        random.seed(
            42
        )  # Seed the random number generator for deterministic entity creation
        """
        Tests that saving a game state and then loading it results in an
        equivalent game state. This confirms serialization and deserialization
        are working correctly.
        """
        save_file = tmp_path / "savegame.json"

        # 1. Create a state, modify it, and save it
        manager_to_save = StateManager()
        manager_to_save.player_manager.move_player(1, 0)
        manager_to_save.game_state.player.xp = 50
        manager_to_save.save_game(str(save_file))

        # 2. Create a new manager by loading from the save file
        # Mock os.path.exists to return True for the save file
        with patch("os.path.exists", return_value=True):
            manager_to_load = StateManager(save_file=str(save_file))

        # 3. Assert that the loaded state matches the saved state
        original_state = manager_to_save.get_game_state()
        loaded_state = manager_to_load.get_game_state()

        assert loaded_state.player.position == original_state.player.position
        assert loaded_state.player.xp == 50
        assert loaded_state.current_turn == original_state.current_turn
        # Compare the dictionaries for a deep comparison
        # Compare the dictionaries for a deep comparison
        assert loaded_state.to_dict() == original_state.to_dict()
