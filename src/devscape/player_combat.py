"""
player_combat.py

Manages the player's combat.
"""

import logging

from devscape.constants import ATTACK_DAMAGE, BASE_REWARD
from devscape.state import Entity, GameState, LLMCharacter, Player


def enemy_retaliate(
    game_state: GameState,
    player: Player,
    enemy: LLMCharacter,
    check_game_over_callback: callable,
) -> None:
    """
    Handles an enemy retaliating against the player.

    Args:
        game_state (GameState): The game state object.
        player (Player): The player being attacked.
        enemy (LLMCharacter): The enemy attacking.
        check_game_over_callback (callable): Callback for checking if the game is over.
    """
    enemy_damage = (
        ATTACK_DAMAGE  # Assuming enemies also use ATTACK_DAMAGE for simplicity
    )
    player.health -= enemy_damage
    game_state.message += f"{enemy.name} retaliated for {enemy_damage} damage. "
    logging.info(
        "%s retaliated for %s damage. Player health: %s.",
        enemy.name,
        enemy_damage,
        player.health,
    )
    check_game_over_callback()


def handle_entity_defeat(
    game_state: GameState,
    player: Player,
    entity: Entity,
    check_level_up_callback: callable,
    update_quests_callback: callable,
) -> None:
    """
    Handles actions after an entity is defeated (e.g., awarding XP, gold).

    Args:
        game_state (GameState): The game state object.
        player (Player): The player who defeated the entity.
        entity (Entity): The defeated entity.
        check_level_up_callback (callable): Callback for checking if the player leveled up.
        update_quests_callback (callable): Callback for updating quests.
    """
    xp_reward = getattr(entity, "xp", 0) + BASE_REWARD
    gold_reward = BASE_REWARD  # Placeholder for gold reward
    player.xp += xp_reward
    player.inventory.gold += gold_reward
    game_state.message += f"You gained {xp_reward} XP and {gold_reward} gold. "
    check_level_up_callback(player)
    update_quests_callback(entity.entity_type)
    logging.info(
        "Player defeated %s, gained %s XP and %s gold.",
        entity.name,
        xp_reward,
        gold_reward,
    )
