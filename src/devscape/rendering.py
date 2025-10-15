"""
rendering.py

Handles all rendering-related functions for the game.
"""

import pygame

from devscape import constants
from devscape.constants import ENTITY_TYPES
from devscape.state import LLMCharacter


def render_pixel_art(surface, pixel_art_lines, rect):
    """
    Render pixel art onto a given surface.

    Args:
        surface (pygame.Surface): The surface to draw on.
        pixel_art_lines (list[str]): ASCII-like lines representing the art.
        rect (pygame.Rect): The rectangle area where the art should be drawn.
    """
    art_height = len(pixel_art_lines)
    if art_height == 0:
        return
    art_width = len(pixel_art_lines[0])
    pixel_w = rect.width / art_width
    pixel_h = rect.height / art_height

    for row_idx, line in enumerate(pixel_art_lines):
        for col_idx, char in enumerate(line):
            color = constants.COLOR_MAP.get(char, constants.BLACK)
            if color != constants.TRANSPARENT:
                pixel_rect = pygame.Rect(
                    rect.left + col_idx * pixel_w,
                    rect.top + row_idx * pixel_h,
                    pixel_w,
                    pixel_h,
                )
                surface.fill(color, pixel_rect)


def draw_text(surface, text, size, rect, color=constants.WHITE):
    """
    Draws text onto a surface, centered above a specified rect.

    Args:
        surface (pygame.Surface): The surface to draw on.
        text (str): The text content to render.
        size (int): The font size.
        rect (pygame.Rect): The rect to position the text relative to.
        color (tuple, optional): The color of the text. Defaults to WHITE.
    """
    font = pygame.font.Font(pygame.font.get_default_font(), size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.center = (rect.centerx, rect.top - 10)
    surface.blit(text_surface, text_rect)


def draw_chat_bubble(
    surface,
    text,
    position,
    font,
    bubble_expires_time=None,
    max_bubble_width=None,
):
    """
    Draw a chat bubble above a character's head.

    Args:
        surface (pygame.Surface): The surface to draw on.
        text (str): The message to display.
        position (tuple): (x, y) coordinates of the character's head.
        font (pygame.font.Font): Font for rendering text.
        bubble_expires_time (int): The tick when the bubble should expire.
        max_bubble_width (int, optional): Maximum width of the bubble.
    """
    padding = 6  # Moved padding definition here
    if not text:
        return

    # If timing is tracked, fade out after duration
    if bubble_expires_time is not None:
        now = pygame.time.get_ticks()
        if now >= bubble_expires_time:
            return  # bubble expired

    # Render text
    wrapped_lines = []
    words = text.split(" ")
    current_line = []
    if max_bubble_width is None:
        max_bubble_width = constants.SCREEN_WIDTH // 3

    for word in words:
        test_line = " ".join(current_line + [word])
        test_width, _ = font.size(test_line)
        if test_width > max_bubble_width and current_line:
            wrapped_lines.append(" ".join(current_line))
            current_line = [word]
        else:
            current_line.append(word)
    wrapped_lines.append(" ".join(current_line))

    text_surfaces = [font.render(line, True, constants.BLACK) for line in wrapped_lines]

    # Calculate bubble dimensions based on wrapped text
    bubble_width = max(ts.get_width() for ts in text_surfaces) + padding * 2
    bubble_height = sum(ts.get_height() for ts in text_surfaces) + padding * 2

    # Position bubble slightly above the character
    bubble_x = position[0] - bubble_width // 2
    bubble_y = position[1] - bubble_height - 10

    # Draw bubble background (white with black border)
    bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)
    pygame.draw.rect(surface, constants.WHITE, bubble_rect, border_radius=8)
    pygame.draw.rect(surface, constants.BLACK, bubble_rect, 2, border_radius=8)

    # Blit text inside bubble
    text_y = bubble_y + padding
    for text_surface in text_surfaces:
        text_x = bubble_x + padding
        surface.blit(text_surface, (text_x, text_y))
        text_y += text_surface.get_height()


def render_dashboard_content(game_instance) -> str:
    """
    Return a string snapshot of the dashboard for the current game state.
    This function is pure: it does not block, print, or wait for input.
    """
    lines = ["=== DevScape Dashboard ==="]

    # Player info
    player = game_instance.state_manager.get_game_state().player
    if player:
        lines.append(f"Player: {player.name} at ({player.x}, {player.y})")

    llm_char = None
    for entity in game_instance.state_manager.get_game_state().entities.values():
        if (
            isinstance(entity, LLMCharacter)
            and entity.entity_type != ENTITY_TYPES["PLAYER"]
        ):
            llm_char = entity
            break
    if llm_char:
        mood = llm_char.mood
        lines.append(f"Mood: {mood}")

        traits = llm_char.traits
        if traits:
            trait_str = ", ".join(f"{k}: {v}" for k, v in traits.items())
            lines.append(f"Traits: {trait_str}")
    else:
        # Graceful fallback when no companion is present
        lines.append("No companion present.")

    # Timeline log
    lines.append("Timeline:")
    if getattr(game_instance, "timeline_log", []):
        for entry in game_instance.timeline_log:
            lines.append(f"- {entry}")
    else:
        lines.append("- (empty)")

    # Event log
    lines.append("Events:")
    if getattr(game_instance, "event_log", []):
        for entry in game_instance.event_log:
            lines.append(f"- {entry}")
    else:
        lines.append("- (empty)")

    # Footer
    lines.append("==========================")

    return "\n".join(lines)
