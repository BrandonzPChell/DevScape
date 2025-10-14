"""
map_manager.py

Manages the game map.
"""

from typing import Any, Dict, Optional, Tuple

from devscape.constants import TILE_COLORS
from devscape.state import GameState, Tile


def get_map_info(game_state: GameState) -> Dict[str, Any]:
    """
    Returns a dictionary containing key map information.

    Returns:
        Dict[str, Any]: Map dimensions and discovered tiles.
    """
    game_map = game_state.game_map
    discovered_tiles = {}
    for y in range(game_map.height):
        for x in range(game_map.width):
            if game_map.tiles[y][x].discovered:
                discovered_tiles[(x, y)] = game_map.tiles[y][x].to_dict()
    return {
        "width": game_map.width,
        "height": game_map.height,
        "discovered_tiles": discovered_tiles,
    }


def get_map_dimensions(game_state: GameState) -> Tuple[int, int]:
    """
    Returns the dimensions of the game map.

    Returns:
        Tuple[int, int]: A tuple (width, height) of the map.
    """
    return game_state.game_map.width, game_state.game_map.height


def get_discovered_locations(game_state: GameState) -> Dict[Tuple[int, int], bool]:
    """
    Returns a dictionary of discovered locations.

    Returns:
        Dict[Tuple[int, int], bool]: Keys are (x, y) tuples, values are always True.
    """
    return game_state.discovered_locations


def get_fow_radius(game_state: GameState) -> int:
    """
    Returns the current Fog of War radius.

    Returns:
        int: The radius of the Fog of War.
    """
    return game_state.fow_radius


def get_tile_at_position(
    game_state: GameState, position: Tuple[int, int]
) -> Optional[Tile]:
    """
    Returns the tile object at a given position.

    Args:
        position (Tuple[int, int]): The (x, y) coordinates of the tile.

    Returns:
        Optional[Tile]: The Tile object if found, otherwise None.
    """
    x, y = position
    if 0 <= x < game_state.game_map.width and 0 <= y < game_state.game_map.height:
        return game_state.game_map.tiles[y][x]
    return None


def get_tile_type_at_position(
    game_state: GameState, position: Tuple[int, int]
) -> Optional[str]:
    """
    Returns the type of the tile at a given position.

    Args:
        position (Tuple[int, int]): The (x, y) coordinates of the tile.

    Returns:
        Optional[str]: The type of the tile (e.g., "GRASS", "WATER"), or None if out of bounds.
    """
    tile = get_tile_at_position(game_state, position)
    return tile.type if tile else None


def get_tile_color_at_position(
    game_state: GameState, position: Tuple[int, int]
) -> Optional[Tuple[int, int, int]]:
    """
    Returns the RGB color of the tile at a given position.

    Args:
        position (Tuple[int, int]): The (x, y) coordinates of the tile.

    Returns:
        Optional[Tuple[int, int, int]]: The RGB color tuple, or None if out of bounds.
    """
    tile: Optional[Tile] = get_tile_at_position(game_state, position)
    if tile:
        color_rgba = TILE_COLORS.get(tile.type)
        if color_rgba:
            return color_rgba[:3]  # type: ignore # type: ignore
    return None


def update_fog_of_war(game_state: GameState) -> None:
    """
    Updates the fog of war based on the player's current position and sight range.
    Tiles within the player's sight range are marked as discovered.
    """
    player_x, player_y = game_state.player.position
    sight_range = game_state.player.sight_range

    for y in range(game_state.game_map.height):
        for x in range(game_state.game_map.width):
            distance = abs(player_x - x) + abs(player_y - y)
            if distance <= sight_range:
                game_state.game_map.tiles[y][x].discovered = True
