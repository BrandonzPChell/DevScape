"""
entity_manager.py

Manages entities in the game.
"""

import random
from typing import Dict, List, Optional, Tuple

from devscape.constants import (
    ENEMY_SIGHT_RANGE,
    ENTITY_COLORS,
    ENTITY_TYPES,
    NPC_DIALOGUE,
    PLAYER_SIGHT_RANGE,
)
from devscape.state import Entity, GameState, LLMCharacter, Map


def place_initial_entities(
    game_map: Map,
    entities: Dict[str, Entity],
    player_position: Tuple[int, int],
) -> None:
    """
    Places initial entities on the map, avoiding the player's starting position.

    Args:
        game_map (Map): The game map.
        entities (Dict[str, Entity]): Dictionary to store entities.
        player_position (Tuple[int, int]): The player's starting position.
    """
    num_enemies = random.randint(3, 7)
    num_npcs = random.randint(1, 3)

    placed_positions = {player_position}

    def get_random_empty_position():
        while True:
            x = random.randint(0, game_map.width - 1)
            y = random.randint(0, game_map.height - 1)
            if (x, y) not in placed_positions:
                placed_positions.add((x, y))
                return (x, y)

    # Place enemies
    for i in range(num_enemies):
        position = get_random_empty_position()
        enemy_id = f"enemy_{i}"
        enemy = LLMCharacter(
            id=enemy_id,
            name=f"Goblin {i}",
            x=position[0],
            y=position[1],
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
            health=random.randint(30, 60),
            max_health=random.randint(30, 60),
            xp=random.randint(10, 20),
            level=random.randint(1, 3),
            sight_range=ENEMY_SIGHT_RANGE,
        )
        entities[enemy_id] = enemy
        game_map.tiles[position[1]][position[0]].entities.append(enemy_id)

    # Place NPCs
    for i in range(num_npcs):
        position = get_random_empty_position()
        npc_id = f"npc_{i}"
        npc_name = random.choice(list(NPC_DIALOGUE.keys()))
        npc = LLMCharacter(
            id=npc_id,
            name=npc_name,
            x=position[0],
            y=position[1],
            art=[
                "..PPP...",
                ".P.P....",
                ".P.P....",
                "..PPP...",
                ".P.P....",
                ".P.P....",
                "PP.PP...",
                "........",
            ],
            health=100,
            max_health=100,
            xp=0,
            level=1,
            dialogue=NPC_DIALOGUE[npc_name],
            entity_type=ENTITY_TYPES["NPC"],
            color=ENTITY_COLORS["NPC"],
            sight_range=PLAYER_SIGHT_RANGE,
        )
        entities[npc_id] = npc
        game_map.tiles[position[1]][position[0]].entities.append(npc_id)


def get_visible_entities(game_state: GameState) -> Dict[str, Entity]:
    """
    Returns a dictionary of entities currently visible to the player.

    Returns:
        Dict[str, Entity]: A dictionary of visible entities, keyed by their ID.
    """
    visible_entities: Dict[str, Entity] = {}
    player_x, player_y = game_state.player.position
    sight_range = game_state.player.sight_range

    for entity_id, entity in game_state.entities.items():
        if entity_id == game_state.player.id:
            continue

        entity_x, entity_y = entity.position
        distance = abs(player_x - entity_x) + abs(player_y - entity_y)

        if distance <= sight_range:
            visible_entities[entity_id] = entity
    return visible_entities


def get_entity_at_position(
    game_state: GameState, position: Tuple[int, int]
) -> List[Entity]:
    """
    Returns a list of entities at a given position.

    Args:
        position (Tuple[int, int]): The (x, y) coordinates of the position.

    Returns:
        List[Entity]: A list of Entity objects at the specified position.
    """
    tile = game_state.game_map.get_tile(position[0], position[1])
    if tile:
        return [
            game_state.entities[eid]
            for eid in tile.entities
            if eid in game_state.entities
        ]
    return []


def get_all_entities(game_state: GameState) -> Dict[str, Entity]:
    """
    Returns a dictionary of all entities in the game.

    Returns:
        Dict[str, Entity]: A dictionary of all entities, keyed by their ID.
    """
    return game_state.entities


def get_entity_by_id(game_state: GameState, entity_id: str) -> Optional[Entity]:
    """
    Returns an entity by its ID.

    Args:
        entity_id (str): The ID of the entity.

    Returns:
        Optional[Entity]: The Entity object if found, otherwise None.
    """
    return game_state.entities.get(entity_id)


def get_entity_color(
    game_state: GameState, entity_id: str
) -> Optional[Tuple[int, int, int]]:
    """
    Returns the RGB color of an entity.

    Args:
        entity_id (str): The ID of the entity.

    Returns:
        Optional[Tuple[int, int, int]]: The RGB color tuple, or None if entity not found.
    """
    entity = get_entity_by_id(game_state, entity_id)
    return entity.color[:3] if entity and entity.color else None


def get_entity_name(game_state: GameState, entity_id: str) -> Optional[str]:
    """
    Returns the name of an entity.

    Args:
        entity_id (str): The ID of the entity.

    Returns:
        Optional[str]: The name of the entity, or None if entity not found.
    """
    entity = get_entity_by_id(game_state, entity_id)
    return entity.name if entity else None


def get_entity_position(
    game_state: GameState, entity_id: str
) -> Optional[Tuple[int, int]]:
    """
    Returns the position of an entity.

    Args:
        entity_id (str): The ID of the entity.

    Returns:
        Optional[Tuple[int, int]]: The (x, y) coordinates of the entity, or None if entity not found.
    """
    entity = get_entity_by_id(game_state, entity_id)
    return entity.position if entity else None


def get_entity_health(game_state: GameState, entity_id: str) -> Optional[int]:
    """
    Returns the health of an entity.

    Args:
        entity_id (str): The ID of the entity.

    Returns:
        Optional[int]: The health of the entity, or None if entity not found or has no health attribute.
    """
    entity = get_entity_by_id(game_state, entity_id)
    return getattr(entity, "health", None)


def get_entity_max_health(game_state: GameState, entity_id: str) -> Optional[int]:
    """
    Returns the maximum health of an entity.

    Args:
        entity_id (str): The ID of the entity.

    Returns:
        Optional[int]: The maximum health of the entity, or None if entity not found or has no max_health attribute.
    """
    entity = get_entity_by_id(game_state, entity_id)
    return getattr(entity, "max_health", None)


def get_entity_xp(game_state: GameState, entity_id: str) -> Optional[int]:
    """
    Returns the XP of an entity.

    Args:
        entity_id (str): The ID of the entity.

    Returns:
        Optional[int]: The XP of the entity, or None if entity not found or has no xp attribute.
    """
    entity = get_entity_by_id(game_state, entity_id)
    return getattr(entity, "xp", None)


def get_entity_level(game_state: GameState, entity_id: str) -> Optional[int]:
    """
    Returns the level of an entity.

    Args:
        entity_id (str): The ID of the entity.

    Returns:
        Optional[int]: The level of the entity, or None if entity not found or has no level attribute.
    """
    entity = get_entity_by_id(game_state, entity_id)
    return getattr(entity, "level", None)


def get_entity_dialogue(game_state: GameState, entity_id: str) -> Optional[str]:
    """
    Returns the dialogue of an entity (if it's an LLMCharacter).

    Args:
        entity_id (str): The ID of the entity.

    Returns:
        Optional[str]: The dialogue string, or None if not an LLMCharacter or no dialogue.
    """
    entity = get_entity_by_id(game_state, entity_id)
    if isinstance(entity, LLMCharacter):
        return entity.dialogue
    return None


def get_entity_type(game_state: GameState, entity_id: str) -> Optional[str]:
    """
    Returns the type of an entity.

    Args:
        entity_id (str): The ID of the entity.

    Returns:
        Optional[str]: The type of the entity (e.g., "ENEMY", "NPC"), or None if entity not found.
    """
    entity = get_entity_by_id(game_state, entity_id)
    return entity.entity_type if entity else None
