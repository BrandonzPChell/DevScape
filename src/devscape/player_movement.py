"""
player_movement.py

Manages the player's movement.
"""

import logging

from devscape.constants import MOVEMENT_COST
from devscape.state import GameState


def move_player(
    game_state: "GameState",
    dx: int,
    dy: int,
    handle_tile_interaction_callback: callable,
    update_fog_of_war_callback: callable,
    check_game_over_callback: callable,
) -> None:
    """


    Moves the player by the given deltas (dx, dy) and updates the game state.





    Args:


        game_state (GameState): The game state object.


        dx (int): Change in x-coordinate.


        dy (int): Change in y-coordinate.


        handle_tile_interaction_callback (callable): Callback for StateManager._handle_tile_interaction.


        update_fog_of_war_callback (callable): Callback for StateManager._update_fog_of_war.


        check_game_over_callback (callable): Callback for StateManager._check_game_over.


    """
    player = game_state.player
    new_x, new_y = player.position[0] + dx, player.position[1] + dy

    if (
        0 <= new_x < game_state.game_map.width
        and 0 <= new_y < game_state.game_map.height
    ):
        # Remove player from old tile
        old_tile = game_state.game_map.tiles[player.position[1]][player.position[0]]
        if player.id in old_tile.entities:
            old_tile.entities.remove(player.id)

        player.position = (new_x, new_y)
        player.health -= MOVEMENT_COST  # Deduct health for movement
        # Add player to new tile
        new_tile = game_state.game_map.tiles[new_y][new_x]
        new_tile.entities.append(player.id)

        handle_tile_interaction_callback(new_tile)
        update_fog_of_war_callback()
        check_game_over_callback()
        game_state.current_turn += 1
        logging.info("Player moved to %s. Health: %s", player.position, player.health)
    else:
        game_state.message = "Cannot move beyond map boundaries."
        logging.warning("Player tried to move out of bounds to (%s, %s).", new_x, new_y)
