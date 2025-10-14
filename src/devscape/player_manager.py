"""
player_manager.py

Manages the player's state and actions.
"""

from typing import Any, Dict, List, Tuple

from devscape.player_combat import enemy_retaliate, handle_entity_defeat
from devscape.player_inventory import collect_resource, pickup_item, use_health_potion
from devscape.player_movement import move_player
from devscape.player_progression import check_level_up, update_quests
from devscape.state import Entity, GameState, Inventory, Item, LLMCharacter, Player


class PlayerManager:
    """Manages the player's state and actions."""

    def __init__(
        self,
        game_state: "GameState",
        handle_tile_interaction_callback: callable,
        update_fog_of_war_callback: callable,
        check_game_over_callback: callable,
        complete_quest_callback: callable,
    ):
        """
        Initializes the PlayerManager.

        Args:
            game_state (GameState): The game state object.
            handle_tile_interaction_callback (callable): Callback for StateManager._handle_tile_interaction.
            update_fog_of_war_callback (callable): Callback for StateManager._update_fog_of_war.
            check_game_over_callback (callable): Callback for StateManager._check_game_over.
            complete_quest_callback (callable): Callback for StateManager._complete_quest.
        """
        self.game_state = game_state
        self._handle_tile_interaction_callback = handle_tile_interaction_callback
        self._update_fog_of_war_callback = update_fog_of_war_callback
        self._check_game_over_callback = check_game_over_callback
        self._complete_quest_callback = complete_quest_callback

    def move_player(self, dx: int, dy: int) -> None:
        move_player(
            self.game_state,
            dx,
            dy,
            self._handle_tile_interaction_callback,
            self._update_fog_of_war_callback,
            self._check_game_over_callback,
        )

    def collect_resource(self, player: Player, resource: Entity) -> None:
        collect_resource(self.game_state, player, resource)

    def pickup_item(self, player: Player, item: Item) -> None:
        pickup_item(self.game_state, player, item, self.use_health_potion)

    def use_health_potion(self, player: Player, potion: Item) -> None:
        use_health_potion(self.game_state, player, potion)

    def enemy_retaliate(self, player: Player, enemy: LLMCharacter) -> None:
        enemy_retaliate(self.game_state, player, enemy, self._check_game_over_callback)

    def handle_entity_defeat(self, player: Player, entity: Entity) -> None:
        handle_entity_defeat(
            self.game_state, player, entity, self.check_level_up, self.update_quests
        )

    def check_level_up(self, player: Player) -> None:
        check_level_up(self.game_state, player)

    def update_quests(self, entity_type: str) -> None:
        update_quests(self.game_state, entity_type, self._complete_quest_callback)

    def get_player_info(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing key player information.

        Returns:
            Dict[str, Any]: Player's name, position, health, XP, level, and inventory summary.
        """
        player = self.game_state.player
        return {
            "name": player.name,
            "position": player.position,
            "health": player.health,
            "max_health": player.max_health,
            "xp": player.xp,
            "level": player.level,
            "gold": player.inventory.gold,
            "inventory_items": [item.name for item in player.inventory.items],
            "sight_range": player.sight_range,
        }

    def _get_player_position(self) -> Tuple[int, int]:
        """
        Returns the player's current position.

        Returns:
            Tuple[int, int]: The (x, y) coordinates of the player.
        """
        return self.game_state.player.position

    def _get_player_inventory(self) -> Inventory:
        """
        Returns the player's inventory.

        Returns:
            Inventory: The player's Inventory object.
        """
        return self.game_state.player.inventory

    def _get_player_health(self) -> int:
        """
        Returns the player's current health.

        Returns:
            int: The player's current health.
        """
        return self.game_state.player.health

    def _get_player_level(self) -> int:
        """
        Returns the player's current level.

        Returns:
            int: The player's current level.
        """
        return self.game_state.player.level

    def _get_player_xp(self) -> int:
        """
        Returns the player's current experience points.

        Returns:
            int: The player's current XP.
        """
        return self.game_state.player.xp

    def _get_player_gold(self) -> int:
        """
        Returns the player's current gold.

        Returns:
            int: The player's current gold.
        """
        return self.game_state.player.inventory.gold

    def _get_player_sight_range(self) -> int:
        """
        Returns the player's current sight range.

        Returns:
            int: The player's sight range.
        """
        return self.game_state.player.sight_range

    def _get_player_max_health(self) -> int:
        """
        Returns the player's maximum health.

        Returns:
            int: The player's maximum health.
        """
        return self.game_state.player.max_health

    def _get_player_inventory_items(self) -> List[Item]:
        """
        Returns a list of items in the player's inventory.

        Returns:
            List[Item]: A list of Item objects in the player's inventory.
        """
        return self.game_state.player.inventory.items

    def _get_player_inventory_max_size(self) -> int:
        """
        Returns the maximum size of the player's inventory.

        Returns:
            int: The maximum number of items the player can carry.
        """
        return self.game_state.player.inventory.max_size

    def _get_player_name(self) -> str:
        """
        Returns the player's name.

        Returns:
            str: The player's name.
        """
        return self.game_state.player.name

    def _get_player_id(self) -> str:
        """
        Returns the player's ID.

        Returns:
            str: The player's ID.
        """
        return self.game_state.player.id
