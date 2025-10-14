from unittest.mock import MagicMock, patch

import pytest

from devscape.constants import (
    ATTACK_DAMAGE,
    BASE_REWARD,
    CRITICAL_HIT_CHANCE,
    CRITICAL_HIT_MULTIPLIER,
    ENTITY_TYPES,
    EVENT_EFFECTS,
    EVENT_TYPES,
    EXPLORATION_REWARD,
    HEALTH_POTION_HEAL,
    ITEM_EFFECTS,
    LEVEL_UP_THRESHOLDS,
    MAP_BOUNDARY_X,
    MAP_BOUNDARY_Y,
    MAX_INVENTORY_SIZE,
    MOVEMENT_COST,
    PLAYER_INITIAL_HEALTH,
    PLAYER_INITIAL_LEVEL,
    PLAYER_INITIAL_POSITION,
    PLAYER_INITIAL_XP,
    PLAYER_SIGHT_RANGE,
    TILE_COLORS,
    WORLD_DIMENSIONS,
)
from devscape.state import (
    Entity,
    GameState,
    Inventory,
    Item,
    LLMCharacter,
    Map,
    Player,
    Quest,
    Tile,
)
from devscape.state_manager import StateManager


@pytest.fixture
def state_manager_with_mock_game_state():
    manager = StateManager()
    real_player = Player(
        id="player_1",
        name="Hero",
        x=0,
        y=0,
        art=[],
        entity_type=ENTITY_TYPES["PLAYER"],
        color=(0, 255, 0),
        health=100,
        max_health=100,
        xp=0,
        level=1,
        inventory=Inventory(max_size=10),
        sight_range=5,
    )
    game_map = Map(width=20, height=15)
    game_map.tiles = [
        [Tile(x=x, y=y, type="GRASS", entities=[]) for x in range(game_map.width)]
        for y in range(game_map.height)
    ]
    manager.game_state = GameState(
        player=real_player,
        game_map=game_map,
        entities={},
        quests=[],
        current_turn=0,
        game_over=False,
        message="",
        active_events=[],
        event_history=[],
        discovered_locations={},
        fow_radius=3,
    )
    return manager


@pytest.fixture
def mock_tile():
    tile = MagicMock(spec=Tile)
    tile.position = (0, 0)
    tile.entities = []
    return tile


def test_handle_tile_interaction_with_resource(
    state_manager_with_mock_game_state, mock_tile
):
    manager = state_manager_with_mock_game_state
    resource_id = "resource_123"
    resource = Entity(
        id=resource_id,
        name="WOOD",
        x=0,
        y=0,
        art=[],
        entity_type=ENTITY_TYPES["RESOURCE"],
        color=(0, 0, 0),
    )
    manager.game_state.entities[resource_id] = resource
    mock_tile.entities.append(resource_id)

    manager._handle_tile_interaction(mock_tile)

    assert len(manager.game_state.player.inventory.items) == 1
    assert manager.game_state.player.inventory.items[0].name == "WOOD"
    assert f"You collected a {resource.name}." in manager.game_state.message
    assert resource_id not in mock_tile.entities
    assert resource_id not in manager.game_state.entities


def test_handle_tile_interaction_with_item(
    state_manager_with_mock_game_state, mock_tile
):
    manager = state_manager_with_mock_game_state
    item_id = "item_123"
    item = Item(
        id=item_id,
        name="HEALTH_POTION",
        description="",
        effect=ITEM_EFFECTS["HEALTH_POTION"],
        entity_type=ENTITY_TYPES["ITEM"],
        color=(0, 0, 0),
    )
    manager.game_state.entities[item_id] = item
    mock_tile.entities.append(item_id)

    manager._handle_tile_interaction(mock_tile)

    assert len(manager.game_state.player.inventory.items) == 0
    assert f"You picked up a {item.name}." in manager.game_state.message
    assert (
        f"You used a {item.name} and restored {HEALTH_POTION_HEAL} health."
        in manager.game_state.message
    )
    assert item_id not in mock_tile.entities
    assert item_id not in manager.game_state.entities


def test_handle_tile_interaction_with_npc(
    state_manager_with_mock_game_state, mock_tile
):
    manager = state_manager_with_mock_game_state
    npc_id = "npc_123"
    npc = LLMCharacter(
        id=npc_id,
        name="Merchant",
        x=0,
        y=0,
        art=[],
        entity_type=ENTITY_TYPES["NPC"],
        color=(0, 0, 0),
        dialogue="Hello!",
    )
    manager.game_state.entities[npc_id] = npc
    mock_tile.entities.append(npc_id)

    manager._handle_tile_interaction(mock_tile)

    assert f"{npc.name}: {npc.dialogue}" in manager.game_state.message


def test_handle_tile_interaction_with_enemy(
    state_manager_with_mock_game_state, mock_tile
):
    manager = state_manager_with_mock_game_state
    enemy_id = "enemy_123"
    enemy = LLMCharacter(
        id=enemy_id,
        name="Goblin",
        x=0,
        y=0,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
    )
    manager.game_state.entities[enemy_id] = enemy
    mock_tile.entities.append(enemy_id)

    manager._handle_tile_interaction(mock_tile)

    assert f"You encountered a {enemy.name}!" in manager.game_state.message


def test_handle_tile_interaction_new_area_discovery(
    state_manager_with_mock_game_state, mock_tile
):
    manager = state_manager_with_mock_game_state
    manager.game_state.discovered_locations = {}
    manager.game_state.player.xp = 0

    manager._handle_tile_interaction(mock_tile)

    assert mock_tile.position in manager.game_state.discovered_locations
    assert manager.game_state.player.xp == EXPLORATION_REWARD
    assert (
        f"You discovered a new area and gained {EXPLORATION_REWARD} XP!"
        in manager.game_state.message
    )
    # Assert _check_level_up was called (difficult to assert directly on private method, but can check side effects)
    # For now, we'll assume it's called if XP is gained.


def test_handle_tile_interaction_random_event_triggered(
    state_manager_with_mock_game_state, mock_tile
):
    manager = state_manager_with_mock_game_state
    with patch("random.random", return_value=0.05):  # Force event trigger
        manager._handle_tile_interaction(mock_tile)
        # Assert that _trigger_random_event was called (check for side effects)
        assert len(manager.game_state.event_history) > 0
        assert "event occurred!" in manager.game_state.message


def test_handle_tile_interaction_random_event_not_triggered(
    state_manager_with_mock_game_state, mock_tile
):
    manager = state_manager_with_mock_game_state
    with patch("random.random", return_value=0.15):  # Prevent event trigger
        manager._handle_tile_interaction(mock_tile)
        assert len(manager.game_state.event_history) == 0
        assert "event occurred!" not in manager.game_state.message


# New tests for move_player
def test_move_player_out_of_bounds_negative_x(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.position = (0, 0)
    manager.player_manager.move_player(-1, 0)
    assert manager.game_state.player.position == (0, 0)  # Position should not change
    assert "Cannot move beyond map boundaries." in manager.game_state.message


def test_move_player_out_of_bounds_positive_x(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.position = (MAP_BOUNDARY_X - 1, 0)
    manager.player_manager.move_player(1, 0)
    assert manager.game_state.player.position == (
        MAP_BOUNDARY_X - 1,
        0,
    )  # Position should not change
    assert "Cannot move beyond map boundaries." in manager.game_state.message


def test_move_player_out_of_bounds_negative_y(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.position = (0, 0)
    manager.player_manager.move_player(0, -1)
    assert manager.game_state.player.position == (0, 0)  # Position should not change
    assert "Cannot move beyond map boundaries." in manager.game_state.message


def test_move_player_out_of_bounds_positive_y(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.position = (0, MAP_BOUNDARY_Y - 1)
    manager.player_manager.move_player(0, 1)
    assert manager.game_state.player.position == (
        0,
        MAP_BOUNDARY_Y - 1,
    )  # Position should not change
    assert "Cannot move beyond map boundaries." in manager.game_state.message


def test_move_player_reduces_health(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    initial_health = manager.game_state.player.health
    manager.game_state.player.position = (0, 0)
    manager.player_manager.move_player(1, 0)
    assert manager.game_state.player.health == initial_health - MOVEMENT_COST


def test_move_player_updates_tile_entities(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player_id = manager.game_state.player.id
    initial_pos = (0, 0)
    new_pos = (1, 0)
    manager.game_state.player.position = initial_pos

    # Mock the tiles to have entities lists
    old_tile_mock = MagicMock(spec=Tile)
    old_tile_mock.entities = [player_id]
    new_tile_mock = MagicMock(spec=Tile)
    new_tile_mock.entities = []

    manager.game_state.game_map.tiles[initial_pos[1]][initial_pos[0]] = old_tile_mock
    manager.game_state.game_map.tiles[new_pos[1]][new_pos[0]] = new_tile_mock

    manager.player_manager.move_player(1, 0)

    assert player_id not in old_tile_mock.entities
    assert player_id in new_tile_mock.entities


def test_move_player_increments_turn(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.current_turn = 0
    manager.game_state.player.position = (0, 0)
    manager.player_manager.move_player(1, 0)
    assert manager.game_state.current_turn == 1


# New tests for attack_entity
def test_attack_entity_invalid_target(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.attack_entity("non_existent_enemy")
    assert "Invalid target." in manager.game_state.message


def test_attack_entity_out_of_range(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    enemy_id = "enemy_123"
    enemy = LLMCharacter(
        id=enemy_id,
        name="Goblin",
        x=10,
        y=10,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
    )
    manager.game_state.entities[enemy_id] = enemy
    manager.game_state.player.position = (0, 0)  # Far away

    manager.attack_entity(enemy_id)
    assert f"{enemy.name} is out of range." in manager.game_state.message


def test_attack_entity_invalid_type(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity_id = "resource_123"
    resource = Entity(
        id=entity_id,
        name="Tree",
        x=0,
        y=1,
        art=[],
        entity_type=ENTITY_TYPES["RESOURCE"],
        color=(0, 0, 0),
    )
    manager.game_state.entities[entity_id] = resource
    manager.game_state.player.position = (0, 0)  # Adjacent

    manager.attack_entity(entity_id)
    assert "Invalid target." in manager.game_state.message


def test_attack_entity_successful_critical_hit(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    enemy_id = "enemy_123"
    enemy = LLMCharacter(
        id=enemy_id,
        name="Goblin",
        x=0,
        y=1,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
        health=50,
        max_health=50,
    )
    manager.game_state.entities[enemy_id] = enemy
    manager.game_state.player.position = (0, 0)  # Adjacent
    manager.game_state.game_map.tiles[enemy.y][enemy.x].entities.append(enemy_id)

    with patch(
        "random.random", return_value=CRITICAL_HIT_CHANCE / 2
    ):  # Force critical hit
        manager.attack_entity(enemy_id)
        expected_damage = int(ATTACK_DAMAGE * CRITICAL_HIT_MULTIPLIER)
        assert enemy.health == 50 - expected_damage
        assert "Critical hit!" in manager.game_state.message
        assert (
            f"You attacked {enemy.name} for {expected_damage} damage."
            in manager.game_state.message
        )
        assert manager.game_state.current_turn == 1


def test_attack_entity_successful_normal_hit(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    enemy_id = "enemy_123"
    enemy = LLMCharacter(
        id=enemy_id,
        name="Goblin",
        x=0,
        y=1,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
        health=50,
        max_health=50,
    )
    manager.game_state.entities[enemy_id] = enemy
    manager.game_state.player.position = (0, 0)  # Adjacent
    manager.game_state.game_map.tiles[enemy.y][enemy.x].entities.append(enemy_id)

    with patch(
        "random.random", return_value=CRITICAL_HIT_CHANCE + 0.1
    ):  # Force normal hit
        manager.attack_entity(enemy_id)
        expected_damage = ATTACK_DAMAGE
        assert enemy.health == 50 - expected_damage
        assert "Critical hit!" not in manager.game_state.message
        assert (
            f"You attacked {enemy.name} for {expected_damage} damage."
            in manager.game_state.message
        )
        assert manager.game_state.current_turn == 1


def test_attack_entity_defeat_enemy(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    enemy_id = "enemy_123"
    enemy = LLMCharacter(
        id=enemy_id,
        name="Goblin",
        x=0,
        y=1,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
        health=ATTACK_DAMAGE - 1,
        max_health=50,
    )
    manager.game_state.entities[enemy_id] = enemy
    manager.game_state.player.position = (0, 0)  # Adjacent
    # Add enemy to the mocked tile's entities list
    manager.game_state.game_map.tiles[enemy.y][enemy.x].entities.append(enemy_id)

    with patch(
        "random.random", return_value=CRITICAL_HIT_CHANCE + 0.1
    ):  # Force normal hit
        with patch.object(
            manager.player_manager, "_update_quests"
        ) as mock_update_quests:
            manager.attack_entity(enemy_id)
            assert f"{enemy.name} defeated!" in manager.game_state.message
            assert enemy_id not in manager.game_state.entities
            # Assert _handle_entity_defeat was called (check for side effects like XP/gold gain)
            assert manager.game_state.player.xp > 0  # Assuming BASE_REWARD is > 0
            assert (
                manager.game_state.player.inventory.gold > 0
            )  # Assuming BASE_REWARD is > 0
            mock_update_quests.assert_called_once_with(enemy.entity_type)


def test_attack_entity_enemy_retaliates(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    enemy_id = "enemy_123"
    enemy = LLMCharacter(
        id=enemy_id,
        name="Goblin",
        x=0,
        y=1,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
        health=50,
        max_health=50,
    )
    manager.game_state.entities[enemy_id] = enemy
    manager.game_state.player.position = (0, 0)  # Adjacent
    initial_player_health = manager.game_state.player.health
    # Add enemy to the mocked tile's entities list
    manager.game_state.game_map.tiles[enemy.y][enemy.x].entities.append(enemy_id)

    with patch(
        "random.random", return_value=CRITICAL_HIT_CHANCE + 0.1
    ):  # Force normal hit
        manager.attack_entity(enemy_id)
        # Enemy should retaliate if not defeated
        assert (
            manager.game_state.player.health == initial_player_health - ATTACK_DAMAGE
        )  # Player takes damage only from retaliation


# New tests for _handle_entity_defeat
def test_handle_entity_defeat_awards_xp_and_gold(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    initial_xp = player.xp
    initial_gold = player.inventory.gold
    defeated_enemy = LLMCharacter(
        id="enemy_defeated",
        name="Defeated Goblin",
        x=0,
        y=0,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
        xp=10,
    )

    manager.player_manager._handle_entity_defeat(player, defeated_enemy)
    assert player.inventory.gold == initial_gold + BASE_REWARD
    assert (
        f"You gained {defeated_enemy.xp + BASE_REWARD} XP and {BASE_REWARD} gold."
        in manager.game_state.message
    )


def test_handle_entity_defeat_checks_level_up(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.xp = 0  # Reset XP for this test
    player.level = 1
    defeated_enemy = LLMCharacter(
        id="enemy_defeated",
        name="Defeated Goblin",
        x=0,
        y=0,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
        xp=100,
    )  # Enough XP to level up

    with patch.object(manager, "_check_level_up") as mock_check_level_up:
        manager.player_manager._handle_entity_defeat(player, defeated_enemy)
        mock_check_level_up.assert_called_once_with(player)


def test_handle_entity_defeat_updates_quests(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    defeated_enemy = LLMCharacter(
        id="enemy_defeated",
        name="Defeated Goblin",
        x=0,
        y=0,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
        xp=10,
    )

    with patch.object(manager.player_manager, "_update_quests") as mock_update_quests:
        manager.player_manager._handle_entity_defeat(player, defeated_enemy)
        mock_update_quests.assert_called_once_with(defeated_enemy.entity_type)


# New tests for _check_level_up
def test_check_level_up_once(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.xp = LEVEL_UP_THRESHOLDS[1]  # Just enough XP to level up to 2
    player.level = 1
    initial_max_health = player.max_health
    initial_sight_range = player.sight_range

    manager._check_level_up(player)

    assert player.level == 2
    assert player.max_health == initial_max_health + 20
    assert player.health == player.max_health  # Full heal
    assert player.sight_range == initial_sight_range + 1
    assert "Congratulations! You reached Level 2!" in manager.game_state.message


def test_check_level_up_multiple_times(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.xp = LEVEL_UP_THRESHOLDS[3] + 10  # Enough XP to level up to 4 and beyond
    player.level = 1
    initial_max_health = player.max_health
    initial_sight_range = player.sight_range

    manager._check_level_up(player)

    assert player.level == 4
    assert player.max_health == initial_max_health + (
        20 * 3
    )  # Leveled up 3 times (1->2, 2->3, 3->4)
    assert player.health == player.max_health  # Full heal
    assert player.sight_range == initial_sight_range + 3
    assert "Congratulations! You reached Level 4!" in manager.game_state.message


def test_check_level_up_not_enough_xp(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.xp = LEVEL_UP_THRESHOLDS[1] - 1  # Not enough XP to level up
    player.level = 1
    initial_max_health = player.max_health
    initial_sight_range = player.sight_range

    manager._check_level_up(player)

    assert player.level == 1
    assert player.max_health == initial_max_health
    assert player.health == 100  # Health should not change if not leveled up
    assert player.sight_range == initial_sight_range
    assert "Congratulations!" not in manager.game_state.message


# New tests for _update_quests
def test_update_quests_progress_update(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="quest_1",
        name="Slay Goblin",
        description="",
        type=ENTITY_TYPES["ENEMY"],
        target_count=3,
        current_progress=0,
        completed=False,
        reward_xp=10,
        reward_gold=5,
    )
    manager.game_state.quests.append(quest)

    manager.player_manager._update_quests(ENTITY_TYPES["ENEMY"])

    assert quest.current_progress == 1
    assert not quest.completed


def test_update_quests_completion(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="quest_1",
        name="Slay Goblin",
        description="",
        type=ENTITY_TYPES["ENEMY"],
        target_count=1,
        current_progress=0,
        completed=False,
        reward_xp=10,
        reward_gold=5,
    )
    manager.game_state.quests.append(quest)

    with patch.object(manager, "_complete_quest") as mock_complete_quest:
        manager.player_manager._update_quests(ENTITY_TYPES["ENEMY"])
        assert quest.current_progress == 1
        assert quest.completed
        mock_complete_quest.assert_called_once_with(quest)


def test_update_quests_not_completed(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="quest_1",
        name="Slay Goblin",
        description="",
        type=ENTITY_TYPES["RESOURCE"],
        target_count=3,
        current_progress=0,
        completed=False,
        reward_xp=10,
        reward_gold=5,
    )
    manager.game_state.quests.append(quest)

    manager.player_manager._update_quests(ENTITY_TYPES["ENEMY"])

    assert quest.current_progress == 0
    assert not quest.completed


# New tests for _complete_quest
def test_complete_quest_awards_rewards(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    initial_xp = player.xp
    initial_gold = player.inventory.gold
    quest = Quest(
        id="quest_1",
        name="Test Quest",
        description="",
        type="",
        target_count=1,
        current_progress=1,
        completed=False,
        reward_xp=20,
        reward_gold=10,
    )

    manager._complete_quest(quest)

    assert player.xp == initial_xp + quest.reward_xp
    assert player.inventory.gold == initial_gold + quest.reward_gold
    assert (
        f"Quest '{quest.name}' completed! You gained {quest.reward_xp} XP and {quest.reward_gold} gold."
        in manager.game_state.message
    )


def test_complete_quest_checks_level_up(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    quest = Quest(
        id="quest_1",
        name="Test Quest",
        description="",
        type="",
        target_count=1,
        current_progress=1,
        completed=False,
        reward_xp=20,
        reward_gold=10,
    )

    with patch.object(manager, "_check_level_up") as mock_check_level_up:
        manager._complete_quest(quest)
        mock_check_level_up.assert_called_once_with(player)


def test_complete_quest_generates_new_quest(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="quest_1",
        name="Test Quest",
        description="",
        type="",
        target_count=1,
        current_progress=1,
        completed=False,
        reward_xp=20,
        reward_gold=10,
    )
    manager.game_state.quests = []  # Ensure quests list is empty before generating

    with patch("random.random", return_value=0.2):  # Force new quest generation
        with patch.object(
            manager,
            "_generate_initial_quests",
            return_value=[
                Quest(
                    id="new_quest",
                    name="New Quest",
                    description="",
                    type="",
                    target_count=1,
                    current_progress=0,
                    completed=False,
                    reward_xp=0,
                    reward_gold=0,
                )
            ],
        ) as mock_generate_initial_quests:
            manager._complete_quest(quest)
            mock_generate_initial_quests.assert_called_once_with(
                manager.game_state.player.level
            )
            assert len(manager.game_state.quests) == 1
            assert "A new quest has appeared!" in manager.game_state.message


def test_complete_quest_does_not_generate_new_quest(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="quest_1",
        name="Test Quest",
        description="",
        type="",
        target_count=1,
        current_progress=1,
        completed=False,
        reward_xp=20,
        reward_gold=10,
    )
    manager.game_state.quests = []  # Ensure quests list is empty before generating

    with patch("random.random", return_value=0.6):  # Prevent new quest generation
        with patch.object(
            manager, "_generate_initial_quests"
        ) as mock_generate_initial_quests:
            manager._complete_quest(quest)
            mock_generate_initial_quests.assert_not_called()
            assert len(manager.game_state.quests) == 0
            assert "A new quest has appeared!" not in manager.game_state.message


# New tests for _trigger_random_event
def test_trigger_random_event_healing_aura(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.health = 50
    player.max_health = 100

    with patch("random.choice", return_value=EVENT_TYPES["HEALING_AURA"]):
        manager._trigger_random_event()

    assert player.health == min(
        player.max_health, 50 + EVENT_EFFECTS["HEALING_AURA"]["heal"]
    )
    assert (
        f"A {EVENT_TYPES['HEALING_AURA']} event occurred!" in manager.game_state.message
    )
    assert len(manager.game_state.event_history) == 1


def test_trigger_random_event_enemy_ambush(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.position = (5, 5)
    initial_entities_count = len(manager.game_state.entities)

    with patch("random.choice", return_value=EVENT_TYPES["ENEMY_AMBUSH"]):
        with patch(
            "random.randint", side_effect=[5, 5, 5, 5, 5, 5]
        ):  # Mock spawn position and enemy stats
            manager._trigger_random_event()

    assert len(manager.game_state.entities) == initial_entities_count + 1
    new_enemy_id = f"enemy_{initial_entities_count}"
    assert new_enemy_id in manager.game_state.entities
    assert "An Ambush Goblin appeared at (5, 5)!" in manager.game_state.message
    assert len(manager.game_state.event_history) == 1


def test_trigger_random_event_treasure_discovery(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.position = (5, 5)
    initial_entities_count = len(manager.game_state.entities)

    with patch("random.choice", return_value=EVENT_TYPES["TREASURE_DISCOVERY"]):
        with patch(
            "random.randint", side_effect=[5, 5]
        ):  # Mock spawn position near player
            manager._trigger_random_event()

    assert len(manager.game_state.entities) == initial_entities_count + 1
    new_item_id = f"item_{initial_entities_count}"
    assert new_item_id in manager.game_state.entities
    assert "You found a Rare Gem at (5, 5)!" in manager.game_state.message
    assert len(manager.game_state.event_history) == 1


# New tests for _check_game_over
def test_check_game_over_player_health_zero(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.health = 0

    with patch("random.choice", return_value="Game Over Message"):
        manager._check_game_over()

    assert manager.game_state.game_over
    assert manager.game_state.message == "Game Over Message"


def test_check_game_over_player_health_above_zero(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.health = 10

    manager._check_game_over()

    assert not manager.game_state.game_over
    assert manager.game_state.message == ""


# New tests for _update_fog_of_war
def test_update_fog_of_war_tiles_discovered(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.position = (5, 5)
    player.sight_range = 1

    # Set all tiles to not discovered initially
    for row in manager.game_state.game_map.tiles:
        for tile in row:
            tile.discovered = False

    manager._update_fog_of_war()

    # Check tiles within sight range
    assert manager.game_state.game_map.tiles[5][5].discovered  # Player's position
    assert manager.game_state.game_map.tiles[5][6].discovered  # Right
    assert manager.game_state.game_map.tiles[5][4].discovered  # Left
    assert manager.game_state.game_map.tiles[6][5].discovered  # Down
    assert manager.game_state.game_map.tiles[4][5].discovered  # Up


def test_update_fog_of_war_tiles_not_discovered(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.position = (5, 5)
    player.sight_range = 1

    # Set all tiles to not discovered initially
    for row in manager.game_state.game_map.tiles:
        for tile in row:
            tile.discovered = False

    manager._update_fog_of_war()

    # Check tiles outside sight range
    assert not manager.game_state.game_map.tiles[5][7].discovered  # Two to the right
    assert not manager.game_state.game_map.tiles[7][5].discovered  # Two down


# New tests for _collect_resource
def test_collect_resource_successful(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    resource = Entity(
        id="resource_1",
        name="WOOD",
        x=0,
        y=0,
        art=[],
        entity_type=ENTITY_TYPES["RESOURCE"],
        color=(0, 0, 0),
    )

    manager.player_manager._collect_resource(player, resource)
    assert player.inventory.items[0].name == "WOOD"
    assert f"You collected a {resource.name}." in manager.game_state.message


def test_collect_resource_inventory_full(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    resource = Entity(
        id="resource_1",
        name="WOOD",
        x=0,
        y=0,
        art=[],
        entity_type=ENTITY_TYPES["RESOURCE"],
        color=(0, 0, 0),
    )
    player.inventory.items = [
        Item(id=f"item_{i}", name="some_item") for i in range(player.inventory.max_size)
    ]

    manager.player_manager._collect_resource(player, resource)

    assert len(player.inventory.items) == player.inventory.max_size
    assert (
        f"Your inventory is full. Cannot collect {resource.name}."
        in manager.game_state.message
    )


# New tests for _pickup_item
def test_pickup_item_successful_no_effect(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    item = Item(
        id="item_1",
        name="SWORD",
        description="",
        effect={},
        entity_type=ENTITY_TYPES["ITEM"],
        color=(0, 0, 0),
    )

    manager._pickup_item(player, item)

    assert len(player.inventory.items) == 1
    assert player.inventory.items[0].name == "SWORD"
    assert f"You picked up a {item.name}." in manager.game_state.message


def test_pickup_item_inventory_full(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    item = Item(
        id="item_1",
        name="SWORD",
        description="",
        effect={},
        entity_type=ENTITY_TYPES["ITEM"],
        color=(0, 0, 0),
    )
    player.inventory.items = [
        Item(id=f"item_{i}", name="some_item") for i in range(player.inventory.max_size)
    ]
    manager.player_manager._pickup_item(player, item)

    assert len(player.inventory.items) == player.inventory.max_size
    assert (
        f"Your inventory is full. Cannot pick up {item.name}."
        in manager.game_state.message
    )


def test_pickup_item_with_heal_effect(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.health = 50
    item = Item(
        id="item_1",
        name="HEALTH_POTION",
        description="",
        effect=ITEM_EFFECTS["HEALTH_POTION"],
        entity_type=ENTITY_TYPES["ITEM"],
        color=(0, 0, 0),
    )

    manager.player_manager._pickup_item(player, item)

    assert len(player.inventory.items) == 0
    assert f"You picked up a {item.name}." in manager.game_state.message
    assert (
        f"You used a {item.name} and restored {HEALTH_POTION_HEAL} health."
        in manager.game_state.message
    )
    assert player.health == min(player.max_health, 50 + HEALTH_POTION_HEAL)


def test_pickup_item_with_gold_effect(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    initial_gold = player.inventory.gold
    item = Item(
        id="item_1",
        name="GOLD_COIN",
        description="",
        effect=ITEM_EFFECTS["GOLD_COIN"],
        entity_type=ENTITY_TYPES["ITEM"],
        color=(0, 0, 0),
    )

    manager.player_manager._pickup_item(player, item)

    assert len(player.inventory.items) == 1
    assert f"You picked up a {item.name}." in manager.game_state.message
    assert (
        f"You gained {ITEM_EFFECTS['GOLD_COIN']['gold']} gold."
        in manager.game_state.message
    )
    assert player.inventory.gold == initial_gold + ITEM_EFFECTS["GOLD_COIN"]["gold"]


# New tests for _use_health_potion
def test_use_health_potion_increases_health(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.health = 50
    potion = Item(
        id="potion_1",
        name="Health Potion",
        description="",
        effect=ITEM_EFFECTS["HEALTH_POTION"],
        entity_type=ENTITY_TYPES["ITEM"],
        color=(0, 0, 0),
    )

    manager.player_manager._use_health_potion(player, potion)

    assert player.health == min(player.max_health, 50 + HEALTH_POTION_HEAL)
    assert (
        f"You used a {potion.name} and restored {HEALTH_POTION_HEAL} health."
        in manager.game_state.message
    )


def test_use_health_potion_at_max_health(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.health = player.max_health
    potion = Item(
        id="potion_1",
        name="Health Potion",
        description="",
        effect=ITEM_EFFECTS["HEALTH_POTION"],
        entity_type=ENTITY_TYPES["ITEM"],
        color=(0, 0, 0),
    )

    manager.player_manager._use_health_potion(player, potion)

    assert player.health == player.max_health
    assert (
        f"You used a {potion.name} and restored {HEALTH_POTION_HEAL} health."
        in manager.game_state.message
    )


# New tests for _enemy_retaliate
def test_enemy_retaliate_reduces_player_health(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    initial_player_health = player.health
    enemy = LLMCharacter(
        id="enemy_1",
        name="Goblin",
        x=0,
        y=0,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
    )
    manager.player_manager._enemy_retaliate(player, enemy)

    assert player.health == initial_player_health - ATTACK_DAMAGE
    assert (
        f"{enemy.name} retaliated for {ATTACK_DAMAGE} damage."
        in manager.game_state.message
    )


def test_enemy_retaliate_checks_game_over(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    enemy = LLMCharacter(
        id="enemy_1",
        name="Goblin",
        x=0,
        y=0,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
    )

    with patch.object(manager, "_check_game_over") as mock_check_game_over:
        manager.player_manager._enemy_retaliate(player, enemy)
        mock_check_game_over.assert_called_once()


# New tests for _new_game
def test_new_game_initializes_player(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    new_game_state = manager._new_game()

    assert new_game_state.player.id == "player_1"
    assert new_game_state.player.name == "Hero"
    assert new_game_state.player.x == PLAYER_INITIAL_POSITION[0]
    assert new_game_state.player.y == PLAYER_INITIAL_POSITION[1]
    assert new_game_state.player.health == PLAYER_INITIAL_HEALTH
    assert new_game_state.player.xp == PLAYER_INITIAL_XP
    assert new_game_state.player.level == PLAYER_INITIAL_LEVEL
    assert new_game_state.player.sight_range == PLAYER_SIGHT_RANGE
    assert isinstance(new_game_state.player.inventory, Inventory)
    assert new_game_state.player.inventory.max_size == MAX_INVENTORY_SIZE


def test_new_game_generates_map(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    new_game_state = manager._new_game()

    assert isinstance(new_game_state.game_map, Map)
    assert new_game_state.game_map.width == WORLD_DIMENSIONS[0]
    assert new_game_state.game_map.height == WORLD_DIMENSIONS[1]
    assert len(new_game_state.game_map.tiles) == WORLD_DIMENSIONS[1]
    assert len(new_game_state.game_map.tiles[0]) == WORLD_DIMENSIONS[0]


def test_new_game_places_initial_entities(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    with patch.object(
        manager, "_place_initial_entities"
    ) as mock_place_initial_entities:
        new_game_state = manager._new_game()
        mock_place_initial_entities.assert_called_once_with(
            new_game_state.game_map,
            new_game_state.entities,
            new_game_state.player.position,
        )


def test_new_game_generates_initial_quests(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    with patch.object(
        manager, "_generate_initial_quests"
    ) as mock_generate_initial_quests:
        new_game_state = manager._new_game()
        mock_generate_initial_quests.assert_called_once_with(
            new_game_state.player.level
        )


def test_new_game_default_game_state_values(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    new_game_state = manager._new_game()

    assert new_game_state.current_turn == 0
    assert not new_game_state.game_over
    assert new_game_state.message == ""
    assert new_game_state.active_events == []
    assert new_game_state.event_history == []
    assert new_game_state.discovered_locations == {}
    assert new_game_state.fow_radius == 3


# New tests for _load_game
def test_load_game_non_existent_file(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    non_existent_file = "non_existent_save.json"

    with patch("devscape.persistence.load_json", return_value={}) as mock_load_json:
        with patch.object(manager, "_new_game") as mock_new_game:
            manager._load_game(non_existent_file)
            mock_load_json.assert_called_once_with(non_existent_file)
            mock_new_game.assert_called_once()


def test_load_game_corrupt_file(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    corrupt_file = "corrupt_save.json"

    with patch("devscape.persistence.load_json", return_value={}) as mock_load_json:
        with patch.object(manager, "_new_game") as mock_new_game:
            manager._load_game(corrupt_file)
            mock_load_json.assert_called_once_with(corrupt_file)
            mock_new_game.assert_called_once()


def test_load_game_successful(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    valid_save_file = "valid_save.json"
    mock_game_state_data = {
        "player": {
            "id": "player_1",
            "name": "Loaded Hero",
            "x": 1,
            "y": 1,
            "art": [],
            "entity_type": "PLAYER",
            "color": [0, 255, 0],
            "health": 90,
            "max_health": 100,
            "xp": 10,
            "level": 2,
            "inventory": {"items": [], "max_size": 10, "gold": 5},
            "sight_range": 6,
        },
        "game_map": {
            "width": 20,
            "height": 15,
            "tiles": [[{"x": 0, "y": 0, "type": "GRASS", "discovered": False}]],
        },
        "entities": {},
        "quests": [],
        "current_turn": 5,
        "game_over": False,
        "message": "Loaded game message",
        "active_events": [],
        "event_history": [],
        "discovered_locations": {"(1, 1)": True},
        "fow_radius": 3,
    }

    with patch(
        "devscape.persistence.load_json", return_value=mock_game_state_data
    ) as mock_load_json:
        with patch(
            "devscape.state_manager.GameState.from_dict",
            return_value=MagicMock(spec=GameState),
        ) as mock_from_dict:
            loaded_game_state = manager._load_game(valid_save_file)
            mock_load_json.assert_called_once_with(valid_save_file)
            mock_from_dict.assert_called_once_with(mock_game_state_data)
            assert loaded_game_state == mock_from_dict.return_value


# New tests for save_game
def test_save_game_successful(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    save_file = "test_save.json"

    with patch("devscape.persistence.save_json") as mock_save_json:
        manager.save_game(save_file)
        mock_save_json.assert_called_once_with(manager.game_state.to_dict(), save_file)
        assert manager.last_save_time is not None


def test_save_game_error(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    save_file = (
        "/non_existent_dir/test_save.json"  # Path that will cause permission error
    )

    with patch(
        "devscape.persistence.save_json", side_effect=Exception("Permission denied")
    ) as mock_save_json:
        with pytest.raises(Exception, match="Permission denied"):
            manager.save_game(save_file)
        mock_save_json.assert_called_once_with(manager.game_state.to_dict(), save_file)


# New tests for get_game_state
def test_get_game_state(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_game_state() == manager.game_state


# New tests for update_game_state
def test_update_game_state(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    new_state = MagicMock(spec=GameState)
    manager.update_game_state(new_state)
    assert manager.game_state == new_state


# New tests for get_visible_entities
def test_get_visible_entities(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    player.position = (0, 0)
    player.sight_range = 1

    visible_enemy = Entity(
        id="enemy_1",
        name="Goblin",
        x=0,
        y=1,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
    )
    far_enemy = Entity(
        id="enemy_2",
        name="Orc",
        x=10,
        y=10,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
    )
    manager.game_state.entities = {
        "player_1": player,
        "enemy_1": visible_enemy,
        "enemy_2": far_enemy,
    }

    visible = manager.get_visible_entities()
    assert "enemy_1" in visible
    assert "enemy_2" not in visible
    assert "player_1" not in visible  # Player should not be in visible entities


# New tests for get_player_info
def test_get_player_info(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player_info = manager.player_manager.get_player_info()
    player = manager.game_state.player

    assert player_info["name"] == player.name
    assert player_info["position"] == player.position
    assert player_info["health"] == player.health
    assert player_info["max_health"] == player.max_health
    assert player_info["xp"] == player.xp
    assert player_info["level"] == player.level
    assert player_info["gold"] == player.inventory.gold
    assert player_info["sight_range"] == player.sight_range
    assert isinstance(player_info["inventory_items"], list)


# New tests for get_map_info
def test_get_map_info(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    game_map = manager.game_state.game_map
    game_map.width = 10
    game_map.height = 5
    game_map.tiles = [
        [
            MagicMock(
                spec=Tile,
                discovered=False,
                position=(x, y),
                to_dict=lambda: {"x": x, "y": y, "type": "GRASS", "discovered": False},
            )
            for x in range(10)
        ]
        for y in range(5)
    ]
    game_map.tiles[0][0].discovered = True
    game_map.tiles[1][1].discovered = True

    map_info = manager.get_map_info()

    assert map_info["width"] == game_map.width
    assert map_info["height"] == game_map.height
    assert (0, 0) in map_info["discovered_tiles"]
    assert (1, 1) in map_info["discovered_tiles"]
    assert (0, 1) not in map_info["discovered_tiles"]


# New tests for get_quest_info
def test_get_quest_info(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest1 = Quest(
        id="q1",
        name="Quest 1",
        description="",
        type="",
        target_count=1,
        current_progress=0,
        completed=False,
        reward_xp=0,
        reward_gold=0,
    )
    quest2 = Quest(
        id="q2",
        name="Quest 2",
        description="",
        type="",
        target_count=1,
        current_progress=0,
        completed=False,
        reward_xp=0,
        reward_gold=0,
    )
    manager.game_state.quests.append(quest1)
    manager.game_state.quests.append(quest2)

    quest_info = manager.get_quest_info()

    assert len(quest_info) == 2
    assert quest_info[0]["id"] == "q1"
    assert quest_info[1]["id"] == "q2"


# New tests for get_game_messages
def test_get_game_messages(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.message = "Test Message"
    assert manager.get_game_messages() == "Test Message"


# New tests for is_game_over
def test_is_game_over(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.game_over = True
    assert manager.is_game_over()
    manager.game_state.game_over = False
    assert not manager.is_game_over()


# New tests for get_event_history
def test_get_event_history(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.event_history = ["Event 1", "Event 2"]
    assert manager.get_event_history() == ["Event 1", "Event 2"]


# New tests for get_tile_at_position
def test_get_tile_at_position_valid(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    tile = manager.get_tile_at_position((0, 0))
    assert tile is not None
    assert tile.position == (0, 0)


def test_get_tile_at_position_invalid(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    tile = manager.get_tile_at_position((-1, -1))
    assert tile is None


# New tests for get_entity_at_position
def test_get_entity_at_position(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity_id = "test_entity"
    entity = Entity(
        id=entity_id,
        name="Test",
        x=0,
        y=0,
        art=[],
        entity_type="GENERIC",
        color=(0, 0, 0),
    )
    manager.game_state.entities[entity_id] = entity
    manager.game_state.game_map.tiles[0][0].entities.append(entity_id)

    entities_at_pos = manager.get_entity_at_position((0, 0))
    assert len(entities_at_pos) == 1
    assert entities_at_pos[0].id == entity_id


def test_get_entity_at_position_empty(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entities_at_pos = manager.get_entity_at_position((0, 0))
    assert len(entities_at_pos) == 0


# New tests for get_player_position
def test_get_player_position(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.position = (5, 5)
    assert manager.player_manager.get_player_position() == (5, 5)


# New tests for get_player_inventory
def test_get_player_inventory(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert (
        manager.player_manager.get_player_inventory()
        == manager.game_state.player.inventory
    )


# New tests for get_player_health
def test_get_player_health(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.health = 75
    assert manager.player_manager.get_player_health() == 75


# New tests for get_player_level
def test_get_player_level(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.level = 3
    assert manager.player_manager.get_player_level() == 3


# New tests for get_player_xp
def test_get_player_xp(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.xp = 150
    assert manager.player_manager.get_player_xp() == 150


# New tests for get_player_gold
def test_get_player_gold(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.inventory.gold = 100
    assert manager.player_manager.get_player_gold() == 100


# New tests for get_all_entities
def test_get_all_entities(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    player = manager.game_state.player
    enemy = Entity(
        id="enemy_1",
        name="Goblin",
        x=0,
        y=0,
        art=[],
        entity_type=ENTITY_TYPES["ENEMY"],
        color=(0, 0, 0),
    )
    manager.game_state.entities = {"player_1": player, "enemy_1": enemy}
    assert manager.get_all_entities() == {"player_1": player, "enemy_1": enemy}


# New tests for get_all_quests
def test_get_all_quests(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="q1",
        name="Quest 1",
        description="",
        type="",
        target_count=1,
        current_progress=0,
        completed=False,
        reward_xp=0,
        reward_gold=0,
    )
    manager.game_state.quests.append(quest)
    assert manager.get_all_quests() == [quest]


# New tests for get_map_dimensions
def test_get_map_dimensions(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.game_map.width = 25
    manager.game_state.game_map.height = 20
    assert manager.get_map_dimensions() == (25, 20)


# New tests for get_discovered_locations
def test_get_discovered_locations(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.discovered_locations = {(1, 1): True, (2, 2): True}
    assert manager.get_discovered_locations() == {(1, 1): True, (2, 2): True}


# New tests for get_fow_radius
def test_get_fow_radius(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.fow_radius = 5
    assert manager.get_fow_radius() == 5


# New tests for get_current_turn
def test_get_current_turn(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.current_turn = 10
    assert manager.get_current_turn() == 10


# New tests for get_active_events
def test_get_active_events(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.active_events = ["Event A", "Event B"]
    assert manager.get_active_events() == ["Event A", "Event B"]


# New tests for get_player_sight_range
def test_get_player_sight_range(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.sight_range = 7
    assert manager.player_manager.get_player_sight_range() == 7


# New tests for get_player_max_health
def test_get_player_max_health(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.max_health = 120
    assert manager.player_manager.get_player_max_health() == 120


# New tests for get_player_inventory_items
def test_get_player_inventory_items(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    item1 = Item(id="i1", name="Item 1", description="", effect={})
    item2 = Item(id="i2", name="Item 2", description="", effect={})
    manager.game_state.player.inventory.items = [item1, item2]
    assert manager.player_manager.get_player_inventory_items() == [item1, item2]


# New tests for get_player_inventory_max_size
def test_get_player_inventory_max_size(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.inventory.max_size = 15
    assert manager.player_manager.get_player_inventory_max_size() == 15


# New tests for get_player_name
def test_get_player_name(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.name = "New Hero"
    assert manager.player_manager.get_player_name() == "New Hero"


# New tests for get_player_id
def test_get_player_id(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.player.id = "new_player_id"
    assert manager.player_manager.get_player_id() == "new_player_id"


# New tests for get_entity_by_id
def test_get_entity_by_id_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = Entity(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="GENERIC",
        color=(0, 0, 0),
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_by_id("e1") == entity


def test_get_entity_by_id_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_entity_by_id("non_existent") is None


# New tests for get_quest_by_id
def test_get_quest_by_id_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="q1",
        name="Quest 1",
        description="",
        type="",
        target_count=1,
        current_progress=0,
        completed=False,
        reward_xp=0,
        reward_gold=0,
    )
    manager.game_state.quests.append(quest)
    assert manager.get_quest_by_id("q1") == quest


def test_get_quest_by_id_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_quest_by_id("non_existent") is None


# New tests for get_tile_type_at_position
def test_get_tile_type_at_position_valid(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.game_map.tiles[0][0].type = "WATER"
    assert manager.get_tile_type_at_position((0, 0)) == "WATER"


def test_get_tile_type_at_position_invalid(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_tile_type_at_position((-1, -1)) is None


# New tests for get_tile_color_at_position
def test_get_tile_color_at_position_valid(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    manager.game_state.game_map.tiles[0][0].type = "GRASS"
    assert manager.get_tile_color_at_position((0, 0)) == TILE_COLORS["GRASS"]


def test_get_tile_color_at_position_invalid(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_tile_color_at_position((-1, -1)) is None


# New tests for get_entity_color
def test_get_entity_color_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = Entity(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="GENERIC",
        color=(1, 2, 3),
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_color("e1") == (1, 2, 3)


def test_get_entity_color_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_entity_color("non_existent") is None


# New tests for get_entity_name
def test_get_entity_name_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = Entity(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="GENERIC",
        color=(0, 0, 0),
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_name("e1") == "Entity 1"


def test_get_entity_name_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_entity_name("non_existent") is None


# New tests for get_entity_position
def test_get_entity_position_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = Entity(
        id="e1",
        name="Entity 1",
        x=5,
        y=5,
        art=[],
        entity_type="GENERIC",
        color=(0, 0, 0),
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_position("e1") == (5, 5)


def test_get_entity_position_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_entity_position("non_existent") is None


# New tests for get_entity_health
def test_get_entity_health_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = LLMCharacter(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="ENEMY",
        color=(0, 0, 0),
        health=50,
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_health("e1") == 50


def test_get_entity_health_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_entity_health("non_existent") is None


def test_get_entity_health_no_health_attribute(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = Entity(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="GENERIC",
        color=(0, 0, 0),
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_health("e1") is None


# New tests for get_entity_max_health
def test_get_entity_max_health_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = LLMCharacter(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="ENEMY",
        color=(0, 0, 0),
        max_health=100,
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_max_health("e1") == 100


def test_get_entity_max_health_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_entity_max_health("non_existent") is None


def test_get_entity_max_health_no_max_health_attribute(
    state_manager_with_mock_game_state,
):
    manager = state_manager_with_mock_game_state
    entity = Entity(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="GENERIC",
        color=(0, 0, 0),
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_max_health("e1") is None


# New tests for get_entity_xp
def test_get_entity_xp_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = LLMCharacter(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="ENEMY",
        color=(0, 0, 0),
        xp=20,
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_xp("e1") == 20


def test_get_entity_xp_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_entity_xp("non_existent") is None


def test_get_entity_xp_no_xp_attribute(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = Entity(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="GENERIC",
        color=(0, 0, 0),
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_xp("e1") is None


# New tests for get_entity_level
def test_get_entity_level_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = LLMCharacter(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="ENEMY",
        color=(0, 0, 0),
        level=2,
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_level("e1") == 2


def test_get_entity_level_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_entity_level("non_existent") is None


def test_get_entity_level_no_level_attribute(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = Entity(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="GENERIC",
        color=(0, 0, 0),
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_level("e1") is None


# New tests for get_entity_dialogue
def test_get_entity_dialogue_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = LLMCharacter(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="NPC",
        color=(0, 0, 0),
        dialogue="Hello",
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_dialogue("e1") == "Hello"


def test_get_entity_dialogue_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_entity_dialogue("non_existent") is None


def test_get_entity_dialogue_not_llm_character(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = Entity(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="GENERIC",
        color=(0, 0, 0),
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_dialogue("e1") is None


# New tests for get_entity_type
def test_get_entity_type_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    entity = Entity(
        id="e1",
        name="Entity 1",
        x=0,
        y=0,
        art=[],
        entity_type="GENERIC",
        color=(0, 0, 0),
    )
    manager.game_state.entities["e1"] = entity
    assert manager.get_entity_type("e1") == "GENERIC"


def test_get_entity_type_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_entity_type("non_existent") is None


# New tests for get_quest_name
def test_get_quest_name_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="q1",
        name="Quest 1",
        description="",
        type="",
        target_count=1,
        current_progress=0,
        completed=False,
        reward_xp=0,
        reward_gold=0,
    )
    manager.game_state.quests.append(quest)
    assert manager.get_quest_name("q1") == "Quest 1"


def test_get_quest_name_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_quest_name("non_existent") is None


# New tests for get_quest_description
def test_get_quest_description_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="q1",
        name="Quest 1",
        description="Description 1",
        type="",
        target_count=1,
        current_progress=0,
        completed=False,
        reward_xp=0,
        reward_gold=0,
    )
    manager.game_state.quests.append(quest)
    assert manager.get_quest_description("q1") == "Description 1"


def test_get_quest_description_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_quest_description("non_existent") is None


# New tests for get_quest_type
def test_get_quest_type_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="q1",
        name="Quest 1",
        description="",
        type="SLAY_ENEMY",
        target_count=1,
        current_progress=0,
        completed=False,
        reward_xp=0,
        reward_gold=0,
    )
    manager.game_state.quests.append(quest)
    assert manager.get_quest_type("q1") == "SLAY_ENEMY"


def test_get_quest_type_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_quest_type("non_existent") is None


# New tests for get_quest_target_count
def test_get_quest_target_count_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="q1",
        name="Quest 1",
        description="",
        type="",
        target_count=5,
        current_progress=0,
        completed=False,
        reward_xp=0,
        reward_gold=0,
    )
    manager.game_state.quests.append(quest)
    assert manager.get_quest_target_count("q1") == 5


def test_get_quest_target_count_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_quest_target_count("non_existent") is None


# New tests for get_quest_current_progress
def test_get_quest_current_progress_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="q1",
        name="Quest 1",
        description="",
        type="",
        target_count=1,
        current_progress=2,
        completed=False,
        reward_xp=0,
        reward_gold=0,
    )
    manager.game_state.quests.append(quest)
    assert manager.get_quest_current_progress("q1") == 2


def test_get_quest_current_progress_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_quest_current_progress("non_existent") is None


# New tests for is_quest_completed
def test_is_quest_completed_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="q1",
        name="Quest 1",
        description="",
        type="",
        target_count=1,
        current_progress=1,
        completed=True,
        reward_xp=0,
        reward_gold=0,
    )
    manager.game_state.quests.append(quest)
    assert manager.is_quest_completed("q1")


def test_is_quest_completed_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.is_quest_completed("non_existent") is None


def test_is_quest_completed_false(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="q1",
        name="Quest 1",
        description="",
        type="",
        target_count=1,
        current_progress=0,
        completed=False,
        reward_xp=0,
        reward_gold=0,
    )
    manager.game_state.quests.append(quest)
    assert not manager.is_quest_completed("q1")


# New tests for get_quest_reward_xp
def test_get_quest_reward_xp_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="q1",
        name="Quest 1",
        description="",
        type="",
        target_count=1,
        current_progress=0,
        completed=False,
        reward_xp=50,
        reward_gold=0,
    )
    manager.game_state.quests.append(quest)
    assert manager.get_quest_reward_xp("q1") == 50


def test_get_quest_reward_xp_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_quest_reward_xp("non_existent") is None


# New tests for get_quest_reward_gold
def test_get_quest_reward_gold_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    quest = Quest(
        id="q1",
        name="Quest 1",
        description="",
        type="",
        target_count=1,
        current_progress=0,
        completed=False,
        reward_xp=0,
        reward_gold=25,
    )
    manager.game_state.quests.append(quest)
    assert manager.get_quest_reward_gold("q1") == 25


def test_get_quest_reward_gold_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_quest_reward_gold("non_existent") is None


# New tests for get_item_name
def test_get_item_name_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    item = Item(id="i1", name="Item 1", description="", effect={})
    manager.game_state.player.inventory.items = [item]
    assert manager.get_item_name("i1") == "Item 1"


def test_get_item_name_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_item_name("non_existent") is None


# New tests for get_item_description
def test_get_item_description_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    item = Item(id="i1", name="Item 1", description="Description 1", effect={})
    manager.game_state.player.inventory.items = [item]
    assert manager.get_item_description("i1") == "Description 1"


def test_get_item_description_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_item_description("non_existent") is None


# New tests for get_item_effect
def test_get_item_effect_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    item = Item(id="i1", name="Item 1", description="", effect={"damage": 5})
    manager.game_state.player.inventory.items = [item]
    assert manager.get_item_effect("i1") == {"damage": 5}


def test_get_item_effect_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_item_effect("non_existent") is None


# New tests for get_item_type
def test_get_item_type_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    item = Item(id="i1", name="Item 1", description="", effect={}, entity_type="WEAPON")
    manager.game_state.player.inventory.items = [item]
    assert manager.get_item_type("i1") == "WEAPON"


def test_get_item_type_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_item_type("non_existent") is None


# New tests for get_item_color
def test_get_item_color_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    item = Item(id="i1", name="Item 1", description="", effect={}, color=(1, 2, 3))
    manager.game_state.player.inventory.items = [item]
    assert manager.get_item_color("i1") == (1, 2, 3)


def test_get_item_color_not_exists(state_manager_with_mock_game_state):
    manager = state_manager_with_mock_game_state
    assert manager.get_item_color("non_existent") is None
