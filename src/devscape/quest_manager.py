"""
quest_manager.py

Manages quests in the game.
"""

import random
from typing import List, Optional

from devscape.constants import QUEST_REWARDS, QUEST_TYPES
from devscape.state import GameState, Quest


def generate_initial_quests(player_level: int) -> List[Quest]:
    """
    Generates initial quests for the player based on their level.

    Args:
        player_level (int): The current level of the player.

    Returns:
        List[Quest]: A list of generated quests.
    """
    quests = []
    num_quests = random.randint(1, 3)
    for i in range(num_quests):
        quest_type = random.choice(list(QUEST_TYPES.keys()))
        target_count = random.randint(1, 5)
        reward_xp = QUEST_REWARDS[quest_type]["xp"] * player_level
        reward_gold = QUEST_REWARDS[quest_type]["gold"] * player_level
        quest = Quest(
            id=f"quest_{i}",
            name=f"{quest_type} Quest",
            description=f"Find and {quest_type.lower()} {target_count} targets.",
            type=quest_type,
            target_count=target_count,
            current_progress=0,
            completed=False,
            reward_xp=reward_xp,
            reward_gold=reward_gold,
        )
        quests.append(quest)
    return quests


def get_quest_info(game_state: GameState) -> List[dict]:
    """
    Returns a list of dictionaries, each containing information about a quest.

    Returns:
        List[Dict[str, Any]]: A list of quests with their details.
    """
    return [quest.to_dict() for quest in game_state.quests]


def get_all_quests(game_state: GameState) -> List[Quest]:
    """
    Returns a list of all quests in the game.

    Returns:
        List[Quest]: A list of all Quest objects.
    """
    return game_state.quests


def get_quest_by_id(game_state: GameState, quest_id: str) -> Optional[Quest]:
    """
    Returns a quest by its ID.

    Args:
        quest_id (str): The ID of the quest.

    Returns:
        Optional[Quest]: The Quest object if found, otherwise None.
    """
    for quest in game_state.quests:
        if quest.id == quest_id:
            return quest
    return None


def get_quest_name(game_state: GameState, quest_id: str) -> Optional[str]:
    """
    Returns the name of a quest.

    Args:
        quest_id (str): The ID of the quest.

    Returns:
        Optional[str]: The name of the quest, or None if quest not found.
    """
    quest = get_quest_by_id(game_state, quest_id)
    return quest.name if quest else None


def get_quest_description(game_state: GameState, quest_id: str) -> Optional[str]:
    """
    Returns the description of a quest.

    Args:
        quest_id (str): The ID of the quest.

    Returns:
        Optional[str]: The description of the quest, or None if quest not found.
    """
    quest = get_quest_by_id(game_state, quest_id)
    return quest.description if quest else None


def get_quest_type(game_state: GameState, quest_id: str) -> Optional[str]:
    """
    Returns the type of a quest.

    Args:
        quest_id (str): The ID of the quest.

    Returns:
        Optional[str]: The type of the quest, or None if quest not found.
    """
    quest = get_quest_by_id(game_state, quest_id)
    return quest.type if quest else None


def get_quest_target_count(game_state: GameState, quest_id: str) -> Optional[int]:
    """
    Returns the target count of a quest.

    Args:
        quest_id (str): The ID of the quest.

    Returns:
        Optional[int]: The target count of the quest, or None if quest not found.
    """
    quest = get_quest_by_id(game_state, quest_id)
    return quest.target_count if quest else None


def get_quest_current_progress(game_state: GameState, quest_id: str) -> Optional[int]:
    """
    Returns the current progress of a quest.

    Args:
        quest_id (str): The ID of the quest.

    Returns:
        Optional[int]: The current progress of the quest, or None if quest not found.
    """
    quest = get_quest_by_id(game_state, quest_id)
    return quest.current_progress if quest else None


def is_quest_completed(game_state: GameState, quest_id: str) -> Optional[bool]:
    """
    Checks if a quest is completed.

    Args:
        quest_id (str): The ID of the quest.

    Returns:
        Optional[bool]: True if the quest is completed, False if not, or None if quest not found.
    """
    quest = get_quest_by_id(game_state, quest_id)
    return quest.completed if quest else None


def get_quest_reward_xp(game_state: GameState, quest_id: str) -> Optional[int]:
    """
    Returns the XP reward of a quest.

    Args:
        quest_id (str): The ID of the quest.

    Returns:
        Optional[int]: The XP reward of the quest, or None if quest not found.
    """
    quest = get_quest_by_id(game_state, quest_id)
    return quest.reward_xp if quest else None


def get_quest_reward_gold(game_state: GameState, quest_id: str) -> Optional[int]:
    """
    Returns the gold reward of a quest.

    Args:
        quest_id (str): The ID of the quest.

    Returns:
        Optional[int]: The gold reward of the quest, or None if quest not found.
    """
    quest = get_quest_by_id(game_state, quest_id)
    return quest.reward_gold if quest else None


def complete_quest(
    game_state: GameState, quest: Quest, check_level_up_callback: callable
) -> None:
    """
    Handles actions upon quest completion (e.g., awarding rewards).

    Args:
        quest (Quest): The completed quest.
    """
    player = game_state.player
    player.xp += quest.reward_xp
    player.inventory.gold += quest.reward_gold
    game_state.message += f" Quest '{quest.name}' completed! You gained {quest.reward_xp} XP and {quest.reward_gold} gold. "
    check_level_up_callback(player)
    # Optionally generate a new quest
    if random.random() < 0.5:  # 50% chance to generate a new quest
        game_state.quests.append(generate_initial_quests(player.level)[0])
        game_state.message += " A new quest has appeared! "
