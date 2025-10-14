"""
player_inventory.py

Manages the player's inventory.
"""

import logging

from devscape.constants import ENTITY_TYPES, HEALTH_POTION_HEAL, ITEM_EFFECTS
from devscape.state import Entity, GameState, Item, Player


def collect_resource(game_state: GameState, player: Player, resource: Entity) -> None:
    """
    Handles the collection of a resource by the player.

    Args:
        game_state (GameState): The game state object.
        player (Player): The player collecting the resource.
        resource (Entity): The resource being collected.
    """
    # Create a new Item object from the resource
    item = Item(
        id=resource.id,
        name=resource.name,
        description=f"A {resource.name} resource.",
        effect=ITEM_EFFECTS.get(resource.name, {}),  # Use resource name to get effects
        entity_type=ENTITY_TYPES["ITEM"],
        color=resource.color,
    )
    if player.inventory.add_item(item):
        game_state.message += f" You collected a {resource.name}."
        logging.info("Player collected resource: %s.", resource.name)
    else:
        game_state.message += (
            f" Your inventory is full. Cannot collect {resource.name}."
        )
        logging.warning("Player inventory full, failed to collect %s.", resource.name)


def pickup_item(
    game_state: GameState,
    player: Player,
    item: Item,
    use_health_potion_callback: callable,
) -> None:
    """
    Handles the player picking up an item.

    Args:
        game_state (GameState): The game state object.
        player (Player): The player picking up the item.
        item (Item): The item being picked up.
        use_health_potion_callback (callable): Callback for using a health potion.
    """
    if player.inventory.add_item(item):
        game_state.message += f" You picked up a {item.name}."
        logging.info("Player picked up item: %s.", item.name)
        # Apply item effects immediately if it's a consumable or has a direct effect
        if item.effect:
            if "heal" in item.effect:
                use_health_potion_callback(player, item)
                player.inventory.remove_item(item.id)  # Remove consumable after use
            if "gold" in item.effect:
                player.inventory.gold += item.effect["gold"]
                game_state.message += f" You gained {item.effect['gold']} gold."
                logging.info(
                    "Player gained %s gold from %s.", item.effect["gold"], item.name
                )
    else:
        game_state.message += f" Your inventory is full. Cannot pick up {item.name}."
        logging.warning("Player inventory full, failed to pick up %s.", item.name)


def use_health_potion(game_state: GameState, player: Player, potion: Item) -> None:
    """
    Applies the effect of a health potion to the player.

    Args:
        game_state (GameState): The game state object.
        player (Player): The player using the potion.
        potion (Item): The health potion item.
    """
    heal_amount = potion.effect.get("heal", HEALTH_POTION_HEAL)
    player.health = min(player.max_health, player.health + heal_amount)
    game_state.message += (
        f" You used a {potion.name} and restored {heal_amount} health."
    )
    logging.info(
        "Player used health potion, restored %s health. Current health: %s.",
        heal_amount,
        player.health,
    )
