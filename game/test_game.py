"""
Tests for the DevScape game, focusing on rendering functions.
"""

import pygame
import pytest
from main import COLOR_MAP, TILE_SIZE, TRANSPARENT, render_pixel_art


@pytest.fixture(scope="module")
def pygame_init():
    """Initializes pygame for the test module and quits it after tests run."""
    pygame.init()
    yield
    pygame.quit()


def test_render_pixel_art_basic(pygame_init):
    """Tests that render_pixel_art correctly draws a basic pattern."""
    # Create a small surface to render on
    surface_width = TILE_SIZE
    surface_height = TILE_SIZE
    surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))  # Fill with transparent black

    # Sample pixel art
    pixel_art = ["X.X", ".X.", "X.X"]

    rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
    render_pixel_art(surface, pixel_art, rect)

    art_height = len(pixel_art)
    art_width = len(pixel_art[0])
    pixel_w = rect.width / art_width
    pixel_h = rect.height / art_height

    # Verify colors
    for row_idx, line in enumerate(pixel_art):
        for col_idx, char in enumerate(line):
            expected_color = COLOR_MAP.get(char, TRANSPARENT)
            check_x = int(rect.left + col_idx * pixel_w + pixel_w / 2)
            check_y = int(rect.top + row_idx * pixel_h + pixel_h / 2)
            actual_color = surface.get_at((check_x, check_y))

            # Pygame's get_at returns a Color object, compare RGB values
            if expected_color == TRANSPARENT:
                # For transparent pixels, we expect the surface to remain transparent
                assert actual_color[3] == 0  # Check alpha channel for transparency
            else:
                assert actual_color[:3] == expected_color[:3]  # Compare RGB
                assert actual_color[3] == 255  # Ensure it's not transparent


def test_render_pixel_art_offset(pygame_init):
    """Tests that render_pixel_art correctly draws at an offset position."""
    surface_width = 10 * TILE_SIZE
    surface_height = 10 * TILE_SIZE
    surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))

    pixel_art = [
        "X",
    ]

    offset_x = 3 * TILE_SIZE
    offset_y = 2 * TILE_SIZE

    rect = pygame.Rect(offset_x, offset_y, TILE_SIZE, TILE_SIZE)
    render_pixel_art(surface, pixel_art, rect)

    # Check the pixel at the offset location
    actual_color = surface.get_at(
        (offset_x + TILE_SIZE // 2, offset_y + TILE_SIZE // 2)
    )
    assert actual_color[:3] == COLOR_MAP["X"][:3]
    assert actual_color[3] == 255

    # Check a pixel outside the rendered area to ensure it's transparent
    actual_color_outside = surface.get_at((0, 0))
    assert actual_color_outside[3] == 0


def test_render_pixel_art_rounding_error(pygame_init):
    """
    Tests that render_pixel_art completely fills the destination rect, even
    when the art dimensions are not perfect divisors of the rect dimensions.
    This test is designed to fail with the original implementation due to
    floating-point rounding errors.
    """
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    surface.fill(TRANSPARENT)

    # Use art dimensions that don't divide TILE_SIZE cleanly (e.g., 7x7)
    pixel_art = ["X" * 7] * 7
    rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
    render_pixel_art(surface, pixel_art, rect)

    # Check the bottom-right pixel. Due to rounding errors, this pixel might
    # not be drawn by the original implementation.
    bottom_right_pixel_color = surface.get_at((TILE_SIZE - 1, TILE_SIZE - 1))

    # The expected color is the one mapped to 'X'
    expected_color = COLOR_MAP["X"]

    # Assert that the pixel is not transparent and has the correct color
    assert bottom_right_pixel_color[3] == 255
    assert bottom_right_pixel_color[:3] == expected_color[:3]
