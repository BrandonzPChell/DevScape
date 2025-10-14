# mypy: ignore-errors
import logging
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from devscape import persistence
from devscape.constants import (
    ATTACK_DAMAGE,
    ATTACK_RANGE,
    CRITICAL_HIT_CHANCE,
    CRITICAL_HIT_MULTIPLIER,
    EXPLORATION_REWARD,
    FOG_OF_WAR_RADIUS,
    GAME_OVER_MESSAGES,
    MAX_INVENTORY_SIZE,
    PLAYER_INITIAL_HEALTH,
    PLAYER_INITIAL_LEVEL,
    PLAYER_INITIAL_POSITION,
    PLAYER_INITIAL_XP,
    PLAYER_SIGHT_RANGE,
    WORLD_DIMENSIONS,
)
from devscape.entity_manager import (
    get_all_entities,
    get_entity_at_position,
    get_entity_by_id,
    get_entity_color,
    get_entity_dialogue,
    get_entity_health,
    get_entity_level,
    get_entity_max_health,
    get_entity_name,
    get_entity_position,
    get_entity_type,
    get_entity_xp,
    get_visible_entities,
    place_initial_entities,
)
from devscape.event_manager import (
    get_active_events,
    get_event_history,
    trigger_random_event,
)
from devscape.map_manager import (
    get_discovered_locations,
    get_fow_radius,
    get_map_dimensions,
    get_map_info,
    get_tile_at_position,
    get_tile_color_at_position,
    get_tile_type_at_position,
    update_fog_of_war,
)
from devscape.player_manager import PlayerManager
from devscape.quest_manager import (
    complete_quest,
    generate_initial_quests,
    get_all_quests,
    get_quest_by_id,
    get_quest_current_progress,
    get_quest_description,
    get_quest_info,
    get_quest_name,
    get_quest_reward_gold,
    get_quest_reward_xp,
    get_quest_target_count,
    get_quest_type,
    is_quest_completed,
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

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class StateManager:
    """
    Manages the game's state, including the player, entities, map, and game progression.
    Provides methods for updating the state, handling events, and managing game mechanics.
    """

    def __init__(self, save_file: Optional[str] = None):
        """
        Initializes the StateManager.

        Args:
            save_file (str, optional): Path to a save file to load the game state from.
                                       If None, a new game state is created.
        """
        self.game_state: GameState = (
            self._load_game(save_file) if save_file else self._new_game()
        )
        self.player_manager = PlayerManager(
            game_state=self.game_state,
            handle_tile_interaction_callback=self._handle_tile_interaction,
            update_fog_of_war_callback=self._update_fog_of_war,
            check_game_over_callback=self._check_game_over,
            complete_quest_callback=self._complete_quest,
        )
        self.last_save_time: float = time.time()
        logging.info("StateManager initialized.")

    def _new_game(self) -> GameState:
        """
        Creates a new game state with initial player, map, and entities.

        Returns:
            GameState: The newly created game state.
        """
        logging.info("Starting a new game.")
        player_id = "player_1"
        initial_player = Player(
            id=player_id,
            name="Hero",
            x=PLAYER_INITIAL_POSITION[0],
            y=PLAYER_INITIAL_POSITION[1],
            art=[
                "..HHHH..",
                ".HSSH...",
                ".HSSSH..",
                "..SCS...",
                "..CCC...",
                "..PPP...",
                ".P.P....",
                ".F.F....",
            ],
            entity_type="PLAYER",
            color=(0, 255, 0),
            health=PLAYER_INITIAL_HEALTH,
            max_health=PLAYER_INITIAL_HEALTH,
            xp=PLAYER_INITIAL_XP,
            level=PLAYER_INITIAL_LEVEL,
            inventory=Inventory(max_size=MAX_INVENTORY_SIZE),
            sight_range=PLAYER_SIGHT_RANGE,
        )
        game_map = Map(WORLD_DIMENSIONS[0], WORLD_DIMENSIONS[1])
        game_map.generate_map()

        # Place initial entities
        entities: Dict[str, Entity] = {player_id: initial_player}
        place_initial_entities(game_map, entities, initial_player.position)

        # Generate initial quests
        quests: List[Quest] = generate_initial_quests(initial_player.level)

        return GameState(
            player=initial_player,
            game_map=game_map,
            entities=entities,
            quests=quests,
            current_turn=0,
            game_over=False,
            message="",
            active_events=[],
            event_history=[],
            discovered_locations={},
            fow_radius=FOG_OF_WAR_RADIUS,
        )

    def _load_game(self, save_file: str) -> GameState:
        """
        Loads a game state from a specified save file using the persistence module.
        If the file doesn't exist or is corrupt, returns a new game state.
        """
        logging.info("Loading game from %s...", save_file)
        data = persistence.load_json(save_file)
        if not data:
            logging.warning(
                "Could not load game from %s. Starting a new game.", save_file
            )
            return self._new_game()

        game_state = GameState.from_dict(data)
        logging.info("Game loaded successfully.")
        return game_state

    def save_game(self, save_file: str) -> None:
        """
        Saves the current game state to a specified file using the persistence module.
        """
        logging.info("Saving game to %s...", save_file)
        try:
            persistence.save_json(self.game_state.to_dict(), save_file)
            self.last_save_time = time.time()
            logging.info("Game saved successfully.")
        except Exception as e:
            logging.error("Error saving game: %s", e)
            raise

    def get_game_state(self) -> GameState:
        """
        Returns the current game state.

        Returns:
            GameState: The current game state object.
        """
        return self.game_state

    def update_game_state(self, new_state: GameState) -> None:
        """
        Updates the entire game state with a new GameState object.

        Args:
            new_state (GameState): The new game state to set.
        """
        self.game_state = new_state
        logging.debug("Game state updated.")

    def _handle_tile_interaction(self, tile: Tile) -> None:
        """
        Handles interactions when the player moves onto a new tile.
        Checks for entities, resources, and triggers events.

        Args:
            tile (Tile): The tile the player moved onto.
        """
        player = self.game_state.player
        self.game_state.message = ""  # Clear previous message

        # Check for entities on the tile
        for entity_id in list(
            tile.entities
        ):  # Iterate over a copy to allow modification
            if entity_id == player.id:
                continue

            entity = self.game_state.entities.get(entity_id)
            if not entity:
                continue

            if entity.entity_type == "RESOURCE":
                self.player_manager.collect_resource(player, entity)
                tile.entities.remove(entity_id)  # Remove resource from tile
                del self.game_state.entities[
                    entity_id
                ]  # Remove resource from game state
            elif entity.entity_type == "ITEM":
                if isinstance(entity, Item):
                    self.player_manager.pickup_item(player, entity)
                    tile.entities.remove(entity_id)  # Remove item from tile
                    del self.game_state.entities[
                        entity_id
                    ]  # Remove item from game state
            elif entity.entity_type == "NPC":
                self.game_state.message = (
                    f"{entity.name}: {getattr(entity, 'dialogue', '...')}"
                )
                logging.info("Player encountered NPC %s.", entity.name)
            elif entity.entity_type == "ENEMY":
                self.game_state.message = f"You encountered a {entity.name}!"
                logging.info("Player encountered enemy %s.", entity.name)

        # Check for exploration reward
        if tile.position not in self.game_state.discovered_locations:
            self.game_state.discovered_locations[tile.position] = True
            player.xp += EXPLORATION_REWARD
            self.game_state.message += (
                f" You discovered a new area and gained {EXPLORATION_REWARD} XP!"
            )
            self.player_manager.check_level_up(player)
            logging.info("Player discovered new area at %s.", tile.position)

        # Trigger random events
        if random.random() < 0.1:  # 10% chance for an event
            trigger_random_event(self.game_state)

    def attack_entity(self, target_id: str) -> None:
        """
        Handles the player attacking an entity.

        Args:
            target_id (str): The ID of the entity to attack.
        """
        player = self.game_state.player
        target = self.game_state.entities.get(target_id)

        if not target or target.entity_type not in [
            "ENEMY",
            "NPC",
        ]:
            self.game_state.message = "Invalid target."
            logging.warning("Player tried to attack invalid target: %s.", target_id)
            return

        distance = abs(player.position[0] - target.position[0]) + abs(
            player.position[1] - target.position[1]
        )
        if distance > ATTACK_RANGE:
            self.game_state.message = f"{target.name} is out of range."
            logging.warning("Player tried to attack %s out of range.", target.name)
            return

        damage = ATTACK_DAMAGE
        if random.random() < CRITICAL_HIT_CHANCE:
            damage = int(damage * CRITICAL_HIT_MULTIPLIER)
            self.game_state.message = "Critical hit! "

        # Ensure target has health attribute before attempting to subtract
        if hasattr(target, "health"):
            target.health -= damage
            self.game_state.message += (
                f"You attacked {target.name} for {damage} damage. "
            )
            logging.info(
                "Player attacked %s for %s damage. %s health: %s.",
                target.name,
                damage,
                target.name,
                getattr(target, "health", "N/A"),
            )

            if target.health <= 0:
                self.game_state.message += f"{target.name} defeated! "
                self.player_manager.handle_entity_defeat(player, target)
                # Remove entity from map and game state
                self.game_state.game_map.tiles[target.position[1]][
                    target.position[0]
                ].entities.remove(target_id)
                del self.game_state.entities[target_id]
                logging.info("%s defeated and removed from game.", target.name)
            else:
                # Enemy retaliates if still alive
                if target.entity_type == "ENEMY":
                    if isinstance(target, LLMCharacter):
                        self.player_manager.enemy_retaliate(player, target)
        else:
            self.game_state.message = f"Cannot attack {target.name}: it has no health."
            logging.warning(
                "Player tried to attack %s which has no health attribute.", target.name
            )

        self._check_game_over()
        self.game_state.current_turn += 1

    def _complete_quest(self, quest: Quest) -> None:
        complete_quest(self.game_state, quest, self.player_manager.check_level_up)

    def _update_fog_of_war(self) -> None:
        update_fog_of_war(self.game_state)

    def _check_game_over(self) -> None:
        """
        Checks if the game-over conditions are met (e.g., player health <= 0).
        """
        if self.game_state.player.health <= 0:
            self.game_state.game_over = True
            self.game_state.message = random.choice(GAME_OVER_MESSAGES)
            logging.info("Game Over: %s", self.game_state.message)

    def get_visible_entities(self) -> Dict[str, Entity]:
        return get_visible_entities(self.game_state)

    def get_map_info(self) -> Dict[str, Any]:
        return get_map_info(self.game_state)

    def get_quest_info(self) -> List[Dict[str, Any]]:
        return get_quest_info(self.game_state)

    def get_game_messages(self) -> str:
        return self.game_state.message

    def is_game_over(self) -> bool:
        return self.game_state.game_over

    def get_event_history(self) -> List[str]:
        return get_event_history(self.game_state)

    def get_tile_at_position(self, position: Tuple[int, int]) -> Optional[Tile]:
        return get_tile_at_position(self.game_state, position)

    def get_entity_at_position(self, position: Tuple[int, int]) -> List[Entity]:
        return get_entity_at_position(self.game_state, position)

    def get_all_entities(self) -> Dict[str, Entity]:
        return get_all_entities(self.game_state)

    def get_all_quests(self) -> List[Quest]:
        return get_all_quests(self.game_state)

    def get_map_dimensions(self) -> Tuple[int, int]:
        return get_map_dimensions(self.game_state)

    def get_discovered_locations(self) -> Dict[Tuple[int, int], bool]:
        return get_discovered_locations(self.game_state)

    def get_fow_radius(self) -> int:
        return get_fow_radius(self.game_state)

    def get_current_turn(self) -> int:
        return self.game_state.current_turn

    def get_active_events(self) -> List[str]:
        return get_active_events(self.game_state)

    def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        return get_entity_by_id(self.game_state, entity_id)

    def get_quest_by_id(self, quest_id: str) -> Optional[Quest]:
        return get_quest_by_id(self.game_state, quest_id)

    def get_tile_type_at_position(self, position: Tuple[int, int]) -> Optional[str]:
        return get_tile_type_at_position(self.game_state, position)

    def get_tile_color_at_position(
        self, position: Tuple[int, int]
    ) -> Optional[Tuple[int, int, int]]:
        return get_tile_color_at_position(self.game_state, position)

    def get_entity_color(self, entity_id: str) -> Optional[Tuple[int, int, int]]:
        return get_entity_color(self.game_state, entity_id)

    def get_entity_name(self, entity_id: str) -> Optional[str]:
        return get_entity_name(self.game_state, entity_id)

    def get_entity_position(self, entity_id: str) -> Optional[Tuple[int, int]]:
        return get_entity_position(self.game_state, entity_id)

    def get_entity_health(self, entity_id: str) -> Optional[int]:
        return get_entity_health(self.game_state, entity_id)

    def get_entity_max_health(self, entity_id: str) -> Optional[int]:
        return get_entity_max_health(self.game_state, entity_id)

    def get_entity_xp(self, entity_id: str) -> Optional[int]:
        return get_entity_xp(self.game_state, entity_id)

    def get_entity_level(self, entity_id: str) -> Optional[int]:
        return get_entity_level(self.game_state, entity_id)

    def get_entity_dialogue(self, entity_id: str) -> Optional[str]:
        return get_entity_dialogue(self.game_state, entity_id)

    def get_entity_type(self, entity_id: str) -> Optional[str]:
        return get_entity_type(self.game_state, entity_id)

    def get_quest_name(self, quest_id: str) -> Optional[str]:
        return get_quest_name(self.game_state, quest_id)

    def get_quest_description(self, quest_id: str) -> Optional[str]:
        return get_quest_description(self.game_state, quest_id)

    def get_quest_type(self, quest_id: str) -> Optional[str]:
        return get_quest_type(self.game_state, quest_id)

    def get_quest_target_count(self, quest_id: str) -> Optional[int]:
        return get_quest_target_count(self.game_state, quest_id)

    def get_quest_current_progress(self, quest_id: str) -> Optional[int]:
        return get_quest_current_progress(self.game_state, quest_id)

    def is_quest_completed(self, quest_id: str) -> Optional[bool]:
        return is_quest_completed(self.game_state, quest_id)

    def get_quest_reward_xp(self, quest_id: str) -> Optional[int]:
        return get_quest_reward_xp(self.game_state, quest_id)

    def get_quest_reward_gold(self, quest_id: str) -> Optional[int]:
        return get_quest_reward_gold(self.game_state, quest_id)

    def get_item_name(self, item_id: str) -> Optional[str]:
        for item in self.game_state.player.inventory.items:
            if item.id == item_id:
                return item.name
        return None

    def get_item_description(self, item_id: str) -> Optional[str]:
        for item in self.game_state.player.inventory.items:
            if item.id == item_id:
                return item.description
        return None

    def get_item_effect(self, item_id: str) -> Optional[Dict[str, Any]]:
        for item in self.game_state.player.inventory.items:
            if item.id == item_id:
                return item.effect
        return None

    def get_item_type(self, item_id: str) -> Optional[str]:
        for item in self.game_state.player.inventory.items:
            if item.id == item_id:
                return item.entity_type
        return None

    def get_item_color(self, item_id: str) -> Optional[Tuple[int, int, int]]:
        for item in self.game_state.player.inventory.items:
            if item.id == item_id:
                return item.color
        return None
