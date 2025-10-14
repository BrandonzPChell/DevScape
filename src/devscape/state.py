"""
state.py

Defines core game state classes and data structures.
"""

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from devscape.constants import ENTITY_TYPES


@dataclass
class Entity:
    """Represents any object in the game world, like players or NPCs."""

    id: str
    name: str
    x: int
    y: int
    art: List[str]
    entity_type: str = "GENERIC"
    color: Tuple[int, int, int, int] = (255, 255, 255, 255)  # Default to white

    # Chat bubble state
    bubble_text: str = ""
    bubble_start_time: int = 0
    bubble_duration: int = 3000  # ms
    bubble_expires: int = 0
    sight_range: int = 0

    @property
    def position(self) -> Tuple[int, int]:
        return (self.x, self.y)

    @position.setter
    def position(self, new_pos: Tuple[int, int]):
        self.x, self.y = new_pos

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "art": self.art,
            "entity_type": self.entity_type,
            "color": self.color,
            "bubble_text": self.bubble_text,
            "bubble_start_time": self.bubble_start_time,
            "bubble_duration": self.bubble_duration,
            "bubble_expires": self.bubble_expires,
            "sight_range": self.sight_range,
        }


@dataclass
class Item(Entity):
    """Represents an item in the game world."""

    id: str = ""
    name: str = ""
    x: int = 0
    y: int = 0
    art: List[str] = field(default_factory=list)
    entity_type: str = "ITEM"
    color: Tuple[int, int, int, int] = (255, 255, 255, 255)  # Default to white
    bubble_text: str = ""
    bubble_start_time: int = 0
    bubble_duration: int = 3000  # ms
    bubble_expires: int = 0
    sight_range: int = 0

    description: str = ""
    effect: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update(
            {
                "description": self.description,
                "effect": self.effect,
            }
        )
        return base_dict


@dataclass
class Inventory:
    """Represents a player's inventory."""

    items: List[Item] = field(default_factory=list)
    max_size: int = 10
    gold: int = 0

    def add_item(self, item: Item) -> bool:
        """Adds an item to the inventory if space is available."""
        if len(self.items) < self.max_size:
            self.items.append(item)
            return True
        return False

    def remove_item(self, item_id: str) -> bool:
        """Removes an item from the inventory by its ID."""
        self.items = [item for item in self.items if item.id != item_id]
        return True

    def get_item(self, item_id: str) -> Optional[Item]:
        """Gets an item from the inventory by its ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def to_dict(self):
        return {
            "items": [item.to_dict() for item in self.items],
            "max_size": self.max_size,
            "gold": self.gold,
        }


@dataclass
class Tile:
    """Represents a single tile on the game map."""

    x: int
    y: int
    type: str = "GRASS"
    discovered: bool = False
    entities: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "type": self.type,
            "discovered": self.discovered,
        }

    @property
    def position(self) -> Tuple[int, int]:
        return (self.x, self.y)


@dataclass
class Map:
    """Represents the game map."""

    width: int
    height: int
    tiles: List[List[Tile]] = field(default_factory=list)

    def generate_map(self):
        """Generates a simple map with grass tiles."""
        self.tiles = [
            [Tile(x, y, type="GRASS") for x in range(self.width)]
            for y in range(self.height)
        ]


@dataclass
class Quest:
    """Represents a quest in the game."""

    id: str
    name: str
    description: str
    type: str
    target_count: int
    current_progress: int = 0
    completed: bool = False
    reward_xp: int = 0
    reward_gold: int = 0

    def to_dict(self):
        return self.__dict__


@dataclass
class LLMCharacter(Entity):
    """Represents the LLM-controlled character's state."""

    health: int = 100
    max_health: int = 100
    xp: int = 0
    level: int = 1
    dialogue: str = ""
    mood: str = "neutral"
    traits: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update(
            {
                "health": self.health,
                "max_health": self.max_health,
                "xp": self.xp,
                "level": self.level,
                "dialogue": self.dialogue,
                "mood": self.mood,
                "traits": self.traits,
            }
        )
        return base_dict


@dataclass
class Player(Entity):
    """Represents the player character's state."""

    health: int = 100
    max_health: int = 100
    xp: int = 0
    level: int = 1
    inventory: "Inventory" = field(
        default_factory=Inventory
    )  # Use lambda for default_factory

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update(
            {
                "health": self.health,
                "max_health": self.max_health,
                "xp": self.xp,
                "level": self.level,
                "inventory": self.inventory.to_dict(),  # Call to_dict on nested Inventory
            }
        )
        return base_dict


@dataclass
class WorldLocation:
    """Represents a discovered location in the world."""

    x: int
    y: int
    name: str = ""
    description: str = ""


@dataclass
class GameState:
    """Represents the overall state of the game."""

    player: "Player"
    game_map: Map
    entities: Dict[str, "Entity"]
    quests: List[Quest]
    current_turn: int = 0
    game_over: bool = False
    message: str = ""
    active_events: List[str] = field(default_factory=list)
    event_history: List[str] = field(default_factory=list)
    discovered_locations: Dict[Tuple[int, int], bool] = field(default_factory=dict)
    fow_radius: int = 3

    def to_dict(self):
        return {
            "player": self.player.to_dict(),
            "game_map": {
                "width": self.game_map.width,
                "height": self.game_map.height,
                "tiles": [
                    [tile.to_dict() for tile in row] for row in self.game_map.tiles
                ],
            },
            "entities": {k: v.to_dict() for k, v in self.entities.items()},
            "quests": [quest.to_dict() for quest in self.quests],
            "current_turn": self.current_turn,
            "game_over": self.game_over,
            "message": self.message,
            "active_events": self.active_events,
            "event_history": self.event_history,
            "discovered_locations": {
                str(k): v for k, v in self.discovered_locations.items()
            },
            "fow_radius": self.fow_radius,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        player_data: Dict[str, Any] = data["player"]
        player = Player(
            id=player_data["id"],
            name=player_data["name"],
            x=player_data["x"],
            y=player_data["y"],
            art=player_data["art"],
            entity_type=player_data["entity_type"],
            color=tuple(player_data["color"]),
            bubble_text=player_data.get("bubble_text", ""),
            bubble_start_time=player_data.get("bubble_start_time", 0),
            bubble_duration=player_data.get("bubble_duration", 3000),
            bubble_expires=player_data.get("bubble_expires", 0),
            health=player_data["health"],
            max_health=player_data["max_health"],
            xp=player_data["xp"],
            level=player_data["level"],
            inventory=Inventory(
                items=[
                    Item(
                        id=item_data["id"],
                        name=item_data["name"],
                        x=item_data["x"],
                        y=item_data["y"],
                        art=item_data["art"],
                        entity_type=item_data["entity_type"],
                        color=(
                            tuple(item_data["color"])
                            if len(item_data["color"]) == 4
                            else tuple(item_data["color"]) + (255,)
                        ),
                        bubble_text=item_data.get("bubble_text", ""),
                        bubble_start_time=item_data.get("bubble_start_time", 0),
                        bubble_duration=item_data.get("bubble_duration", 3000),
                        bubble_expires=item_data.get("bubble_expires", 0),
                        sight_range=item_data.get("sight_range", 0),
                        description=item_data["description"],
                        effect=item_data["effect"],
                    )
                    for item_data in player_data["inventory"]["items"]
                ],
                max_size=player_data["inventory"]["max_size"],
                gold=player_data["inventory"]["gold"],
            ),
            sight_range=player_data["sight_range"],
        )

        game_map_data = data["game_map"]
        game_map = Map(game_map_data["width"], game_map_data["height"])
        game_map.tiles = [
            [Tile(**tile_data) for tile_data in row_data]
            for row_data in game_map_data["tiles"]
        ]

        entities: Dict[str, Entity] = {}  # Explicitly type the dictionary
        for entity_id, entity_data in data["entities"].items():

            entity: Entity  # Declare entity before the conditional
            if entity_data["entity_type"] == "PLAYER":
                # Player is already created, skip
                continue
            if (
                entity_data["entity_type"] == ENTITY_TYPES["ENEMY"]
                or entity_data["entity_type"] == ENTITY_TYPES["NPC"]
            ):
                entity = LLMCharacter(
                    id=entity_data["id"],
                    name=entity_data["name"],
                    x=entity_data["x"],
                    y=entity_data["y"],
                    art=entity_data["art"],
                    entity_type=entity_data["entity_type"],
                    color=(
                        tuple(entity_data["color"])
                        if len(entity_data["color"]) == 4
                        else tuple(entity_data["color"]) + (255,)
                    ),
                    health=entity_data["health"],
                    max_health=entity_data["max_health"],
                    xp=entity_data["xp"],
                    level=entity_data["level"],
                    dialogue=entity_data["dialogue"],
                    mood=entity_data["mood"],
                    traits=entity_data.get("traits", {}),
                    bubble_text=entity_data.get("bubble_text", ""),
                    bubble_start_time=entity_data.get("bubble_start_time", 0),
                    bubble_duration=entity_data.get("bubble_duration", 3000),
                    bubble_expires=entity_data.get("bubble_expires", 0),
                    sight_range=entity_data.get("sight_range", 0),
                )
            else:  # This will now handle generic Entity types
                entity = Entity(
                    id=entity_data["id"],
                    name=entity_data["name"],
                    x=entity_data["x"],
                    y=entity_data["y"],
                    art=entity_data["art"],
                    entity_type=entity_data["entity_type"],
                    color=tuple(entity_data["color"]),
                    bubble_text=entity_data.get("bubble_text", ""),
                    bubble_start_time=entity_data.get("bubble_start_time", 0),
                    bubble_duration=entity_data.get("bubble_duration", 3000),
                    bubble_expires=entity_data.get("bubble_expires", 0),
                    sight_range=entity_data.get("sight_range", 0),
                )
            entities[entity_id] = entity
        entities[player.id] = player  # Add player to entities dictionary

        quests = [Quest(**quest_data) for quest_data in data["quests"]]

        discovered_locations = {
            ast.literal_eval(k): v for k, v in data["discovered_locations"].items()
        }

        return cls(
            player=player,
            game_map=game_map,
            entities=entities,
            quests=quests,
            current_turn=data["current_turn"],
            game_over=data["game_over"],
            message=data["message"],
            active_events=data["active_events"],
            event_history=data["event_history"],
            discovered_locations=discovered_locations,
            fow_radius=data["fow_radius"],
        )
