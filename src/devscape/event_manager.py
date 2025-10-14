"""
event_manager.py

Manages events in the game.
"""

import random
from typing import List

from devscape.constants import (
    ENEMY_SIGHT_RANGE,
    ENTITY_COLORS,
    ENTITY_TYPES,
    EVENT_DESCRIPTIONS,
    EVENT_EFFECTS,
    EVENT_TYPES,
    MAP_BOUNDARY_X,
    MAP_BOUNDARY_Y,
)
from devscape.state import GameState, Item, LLMCharacter


def trigger_random_event(game_state: GameState) -> None:
    """
    Triggers a random game event that can affect the player or world.
    """
    event_type = random.choice(list(EVENT_TYPES.keys()))
    event_description = EVENT_DESCRIPTIONS[event_type]
    event_effect = EVENT_EFFECTS[event_type]

    game_state.message += f" A {event_type} event occurred! {event_description} "
    game_state.event_history.append(
        f"Turn {game_state.current_turn}: {event_description}"
    )

    # Apply event effects
    if event_type == EVENT_TYPES["HEALING_AURA"]:
        game_state.player.health = min(
            game_state.player.max_health,
            game_state.player.health + event_effect["heal"],
        )
        game_state.message += f" You healed {event_effect['heal']} health. "
    elif event_type == EVENT_TYPES["ENEMY_AMBUSH"]:
        # Spawn a new enemy near the player
        player_pos = game_state.player.position
        spawn_x = random.randint(
            max(0, player_pos[0] - 2), min(MAP_BOUNDARY_X - 1, player_pos[0] + 2)
        )
        spawn_y = random.randint(
            max(0, player_pos[1] - 2), min(MAP_BOUNDARY_Y - 1, player_pos[1] + 2)
        )
        enemy_id = f"enemy_{len(game_state.entities)}"
        enemy = LLMCharacter(
            id=enemy_id,
            name="Ambush Goblin",
            x=spawn_x,
            y=spawn_y,
            art=[
                "..RRR...",
                ".RRRRR..",
                ".RR.RR..",
                "..RRR...",
                ".R.R....",
                ".R...R..",
                "RR...RR.",
                "........",
            ],
            health=random.randint(40, 70),
            max_health=random.randint(40, 70),
            xp=random.randint(15, 25),
            level=random.randint(2, 4),
            dialogue="Surprise!",
            entity_type=ENTITY_TYPES["ENEMY"],
            color=ENTITY_COLORS["ENEMY"],
            sight_range=ENEMY_SIGHT_RANGE,
        )
        game_state.entities[enemy_id] = enemy
        game_state.game_map.tiles[spawn_y][spawn_x].entities.append(enemy_id)
        game_state.message += f" An {enemy.name} appeared at ({spawn_x}, {spawn_y})! "
    elif event_type == EVENT_TYPES["TREASURE_DISCOVERY"]:
        # Spawn a valuable item near the player
        player_pos = game_state.player.position
        spawn_x = random.randint(
            max(0, player_pos[0] - 1), min(MAP_BOUNDARY_X - 1, player_pos[0] + 1)
        )
        spawn_y = random.randint(
            max(0, player_pos[1] - 1), min(MAP_BOUNDARY_Y - 1, player_pos[1] + 1)
        )
        item_id = f"item_{len(game_state.entities)}"
        item = Item(
            id=item_id,
            name="Rare Gem",
            description="A sparkling rare gem, worth a lot of gold!",
            effect={"gold": 50},
            entity_type=ENTITY_TYPES["ITEM"],
            color=ENTITY_COLORS["ITEM"],
        )
        game_state.entities[item_id] = item
        game_state.game_map.tiles[spawn_y][spawn_x].entities.append(item_id)
        game_state.message += f" You found a {item.name} at ({spawn_x}, {spawn_y})! "


def get_event_history(game_state: GameState) -> List[str]:
    """
    Returns the history of game events.

    Returns:
        List[str]: A list of strings, each describing a past event.
    """
    return game_state.event_history


def get_active_events(game_state: GameState) -> List[str]:
    """
    Returns a list of currently active game events.

    Returns:
        List[str]: A list of strings, each describing an active event.
    """
    return game_state.active_events
