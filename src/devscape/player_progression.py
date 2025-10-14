"""
player_progression.py

Manages the player's progression.
"""

import logging

from devscape.constants import LEVEL_UP_THRESHOLDS
from devscape.state import GameState, Player


def check_level_up(game_state: GameState, player: Player) -> None:
    """
    Checks if the player has enough XP to level up and applies level-up benefits.

    Args:
        game_state (GameState): The game state object.
        player (Player): The player to check for level up.
    """
    while (
        player.level < len(LEVEL_UP_THRESHOLDS)
        and player.xp >= LEVEL_UP_THRESHOLDS[player.level]
    ):
        player.level += 1
        player.max_health += 20  # Example: Increase max health on level up
        player.health = player.max_health  # Fully heal on level up
        player.sight_range += 1  # Increase sight range
        game_state.message += f" Congratulations! You reached Level {player.level}! "
        logging.info("Player leveled up to %s.", player.level)


def update_quests(
    game_state: GameState, entity_type: str, complete_quest_callback: callable
) -> None:
    """
    Updates quest progress based on the type of entity defeated or action performed.

    Args:
        game_state (GameState): The game state object.
        entity_type (str): The type of entity defeated (e.g., "ENEMY", "RESOURCE").
        complete_quest_callback (callable): Callback for completing a quest.
    """
    for quest in game_state.quests:
        if not quest.completed and quest.type == entity_type:
            quest.current_progress += 1
            if quest.current_progress >= quest.target_count:
                quest.completed = True
                complete_quest_callback(quest)
                logging.info("Quest '%s' completed.", quest.name)
