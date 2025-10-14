"""Tests for the draw_text function in game.rendering."""

from unittest.mock import MagicMock, patch

from devscape.constants import WHITE
from devscape.rendering import draw_text


@patch("devscape.rendering.pygame.font.Font")
@patch("devscape.rendering.pygame.font.get_default_font", return_value="default_font")
def test_draw_text(_mock_get_default_font, mock_font):
    mock_surface = MagicMock()
    mock_rect = MagicMock(centerx=100, top=50)
    mock_text_surface = MagicMock()
    mock_text_rect = MagicMock()

    mock_font.return_value.render.return_value = mock_text_surface
    mock_text_surface.get_rect.return_value = mock_text_rect

    draw_text(mock_surface, "Test Text", 20, mock_rect)

    mock_font.assert_called_with("default_font", 20)
    mock_font.return_value.render.assert_called_with("Test Text", True, WHITE)
    mock_text_surface.get_rect.assert_called_once()
    assert mock_text_rect.center == (mock_rect.centerx, mock_rect.top - 10)
    mock_surface.blit.assert_called_with(mock_text_surface, mock_text_rect)
