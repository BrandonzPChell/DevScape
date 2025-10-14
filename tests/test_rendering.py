import os

os.environ["SDL_VIDEODRIVER"] = "dummy"

import unittest
from unittest.mock import ANY, Mock, patch

import pygame

from devscape import constants
from devscape.rendering import (
    draw_chat_bubble,
    draw_text,
    render_dashboard_content,
    render_pixel_art,
)
from devscape.state import LLMCharacter


class TestRenderPixelArt(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1, 1), pygame.HIDDEN)

    def tearDown(self):
        pygame.quit()

    @patch("pygame.Surface")
    @patch("pygame.Rect")
    def test_render_pixel_art_basic(self, mock_rect_class, mock_surface_class):
        mock_surface = Mock()
        mock_rect = Mock()
        mock_rect_class.return_value = mock_rect

        pixel_art_lines = [" X ", "XOX", " X "]
        rect = Mock(x=0, y=0, width=30, height=30, left=0, top=0)

        render_pixel_art(mock_surface, pixel_art_lines, rect)

        # Verify surface.fill calls
        assert mock_surface.fill.call_count == 5

        # More detailed assertion for specific calls would require matching the rects
        # For now, we'll just check the call count and colors
        called_colors = [call[0][0] for call in mock_surface.fill.call_args_list]
        assert called_colors.count(constants.WHITE) == 4
        assert called_colors.count(constants.BLACK) == 1

    @patch("pygame.font.Font")
    @patch("pygame.font.get_default_font")
    @patch("pygame.Surface")
    @patch("pygame.Rect")
    def test_draw_text_basic(
        self,
        mock_rect_class,
        mock_surface_class,
        mock_get_default_font,
        mock_font_class,
    ):
        mock_surface = Mock()
        mock_rect = Mock(centerx=100, top=50)
        mock_font_instance = Mock()
        mock_font_class.return_value = mock_font_instance
        mock_font_instance.render.return_value = Mock(
            get_rect=Mock(return_value=Mock())
        )

        text = "Hello World"
        size = 20
        color = constants.RED

        draw_text(mock_surface, text, size, mock_rect, color)

        mock_get_default_font.assert_called_once()
        mock_font_class.assert_called_once_with(
            mock_get_default_font.return_value, size
        )
        mock_font_instance.render.assert_called_once_with(text, True, color)
        mock_surface.blit.assert_called_once()

    @patch("pygame.Surface")
    @patch("pygame.Rect")
    def test_render_pixel_art_empty_lines(self, mock_rect_class, mock_surface_class):
        mock_surface = Mock()
        pixel_art_lines = []
        rect = Mock(x=0, y=0, width=30, height=30, left=0, top=0)

        render_pixel_art(mock_surface, pixel_art_lines, rect)

        mock_surface.fill.assert_not_called()


@patch("pygame.time.get_ticks", return_value=0)
@patch("pygame.draw.rect")
@patch("pygame.font.Font")
@patch("pygame.Surface")
@patch("pygame.Rect")
class TestDrawChatBubble(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1, 1), pygame.HIDDEN)

    def tearDown(self):
        pygame.quit()

    def test_draw_chat_bubble_basic(
        self,
        mock_rect_class,
        mock_surface_class,
        mock_font_class,
        mock_draw_rect,
        mock_get_ticks,
    ):
        mock_surface = Mock()
        mock_surface.get_width.return_value = 800  # Mock get_width for the main surface
        mock_font = Mock()
        mock_font_class.return_value = mock_font
        mock_font.size.return_value = (50, 20)  # Mock font.size to return a tuple
        mock_font.render.return_value = Mock(
            get_rect=Mock(return_value=Mock(x=0, y=0, width=50, height=20)),
            get_width=Mock(return_value=50),
            get_height=Mock(
                return_value=20
            ),  # Add get_height to the mocked text_surface
        )

        text = "Hello"
        position = (100, 100)
        font = mock_font

        draw_chat_bubble(mock_surface, text, position, font)

        # Verify that the bubble background is drawn
        mock_draw_rect.assert_any_call(
            mock_surface, constants.WHITE, ANY, border_radius=8
        )
        mock_draw_rect.assert_any_call(
            mock_surface, constants.BLACK, ANY, 2, border_radius=8
        )

        # Verify text rendering
        mock_font.render.assert_called_with(text, True, constants.BLACK)
        mock_surface.blit.assert_called_once()

    def test_draw_chat_bubble_empty_text(
        self,
        mock_rect_class,
        mock_surface_class,
        mock_font_class,
        mock_draw_rect,
        mock_get_ticks,
    ):
        mock_surface = Mock()
        mock_font = Mock()

        text = ""
        position = (100, 100)
        font = mock_font

        draw_chat_bubble(mock_surface, text, position, font)

        # No drawing should happen for empty text
        mock_draw_rect.assert_not_called()
        mock_font.render.assert_not_called()
        mock_surface.blit.assert_not_called()

    def test_draw_chat_bubble_expired(
        self,
        mock_rect_class,
        mock_surface_class,
        mock_font_class,
        mock_draw_rect,
        mock_get_ticks,
    ):
        mock_surface = Mock()
        mock_font = Mock()
        mock_get_ticks.return_value = 1000  # Current time is 1000

        text = "Expired"
        position = (100, 100)
        bubble_expires_time = 500  # Bubble expired at 500
        font = mock_font

        draw_chat_bubble(
            mock_surface,
            text,
            position,
            font,
            bubble_expires_time=bubble_expires_time,
        )

        # No drawing should happen for expired bubble
        mock_draw_rect.assert_not_called()
        mock_font.render.assert_not_called()
        mock_surface.blit.assert_not_called()

    def test_draw_chat_bubble_not_expired(
        self,
        mock_rect_class,
        mock_surface_class,
        mock_font_class,
        mock_draw_rect,
        mock_get_ticks,
    ):
        mock_surface = Mock()
        mock_surface.get_width.return_value = 800  # Mock get_width for the main surface
        mock_font = Mock()
        mock_font_class.return_value = mock_font
        mock_font.size = Mock(return_value=(50, 20))
        mock_font.render.return_value = Mock(
            get_rect=Mock(return_value=Mock(x=0, y=0, width=50, height=20)),
            get_width=Mock(return_value=50),
            get_height=Mock(return_value=20),
        )
        mock_get_ticks.return_value = 500  # Current time is 500

        text = "Not Expired"
        position = (100, 100)
        bubble_expires_time = 1000  # Bubble expires at 1000
        font = mock_font

        draw_chat_bubble(
            mock_surface,
            text,
            position,
            font,
            bubble_expires_time=bubble_expires_time,
        )

        # Drawing should happen for not expired bubble
        mock_draw_rect.assert_any_call(
            mock_surface, constants.WHITE, ANY, border_radius=8
        )
        mock_draw_rect.assert_any_call(
            mock_surface, constants.BLACK, ANY, 2, border_radius=8
        )
        mock_font.render.assert_called_with(text, True, constants.BLACK)
        mock_surface.blit.assert_called_once()

    def test_draw_chat_bubble_text_wrapping(
        self,
        mock_rect_class,
        mock_surface_class,
        mock_font_class,
        mock_draw_rect,
        mock_get_ticks,
    ):
        mock_surface = Mock()
        mock_surface.get_width.return_value = 800  # Mock get_width for the main surface
        mock_font = Mock()
        mock_font_class.return_value = mock_font

        # Mock font.size to simulate wrapping
        mock_font.size = Mock(
            side_effect=[
                (50, 20),  # "Word1"
                (100, 20),  # "Word1 Word2"
                (50, 20),  # "Word2"
                (100, 20),  # "Word2 Word3"
                (50, 20),  # "Word3"
            ]
        )
        mock_font.render.side_effect = [
            Mock(
                get_rect=Mock(return_value=Mock(x=0, y=0, width=50, height=20)),
                get_width=Mock(return_value=50),
                get_height=Mock(return_value=20),
            ),
            Mock(
                get_rect=Mock(return_value=Mock(x=0, y=0, width=50, height=20)),
                get_width=Mock(return_value=50),
                get_height=Mock(return_value=20),
            ),
            Mock(
                get_rect=Mock(return_value=Mock(x=0, y=0, width=50, height=20)),
                get_width=Mock(return_value=50),
                get_height=Mock(return_value=20),
            ),
        ]

        text = "Word1 Word2 Word3"
        position = (100, 100)
        max_bubble_width = 70  # Force wrapping

        draw_chat_bubble(
            mock_surface, text, position, mock_font, max_bubble_width=max_bubble_width
        )

        # Verify that render is called for wrapped lines
        assert mock_font.render.call_count == 2
        mock_font.render.assert_any_call("Word1", True, constants.BLACK)
        mock_font.render.assert_any_call("Word2 Word3", True, constants.BLACK)

        # Verify blit is called for each line
        assert mock_surface.blit.call_count == 2


class TestRenderDashboardContent(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1, 1), pygame.HIDDEN)

    def tearDown(self):
        pygame.quit()

    def test_render_dashboard_content_basic(self):
        mock_player = Mock(name="Player", x=10, y=20)
        mock_player.name = "Player"  # Set the name explicitly
        mock_llm_character = Mock(
            spec=LLMCharacter, mood="Happy", traits={"brave": 10, "kind": 5}
        )
        mock_llm_character.entity_type = constants.ENTITY_TYPES["NPC"]

        mock_entities_values = Mock(return_value=[mock_player, mock_llm_character])
        mock_entities = Mock(values=mock_entities_values)
        mock_game_state_returned = Mock(player=mock_player, entities=mock_entities)

        mock_state_manager = Mock(
            get_game_state=Mock(return_value=mock_game_state_returned)
        )

        mock_game_instance = Mock(
            state_manager=mock_state_manager,
            timeline_log=["Event 1", "Event 2"],
            event_log=["Log 1", "Log 2"],
        )

        expected_output = (
            "=== DevScape Dashboard ===\n"
            "Player: Player at (10, 20)\n"
            "Mood: Happy\n"
            "Traits: brave: 10, kind: 5\n"
            "Timeline:\n"
            "- Event 1\n"
            "- Event 2\n"
            "Events:\n"
            "- Log 1\n"
            "- Log 2\n"
            "=========================="
        )

        result = render_dashboard_content(mock_game_instance)
        self.assertEqual(result, expected_output)

    def test_render_dashboard_content_no_player(self):
        mock_llm_character = Mock(
            spec=LLMCharacter, mood="Happy", traits={"brave": 10, "kind": 5}
        )
        mock_llm_character.entity_type = constants.ENTITY_TYPES["NPC"]

        mock_entities_values = Mock(return_value=[mock_llm_character])
        mock_entities = Mock(values=mock_entities_values)
        mock_game_state_returned = Mock(player=None, entities=mock_entities)

        mock_state_manager = Mock(
            get_game_state=Mock(return_value=mock_game_state_returned)
        )

        mock_game_instance = Mock(
            state_manager=mock_state_manager,
            timeline_log=[],
            event_log=[],
        )

        expected_output = (
            "=== DevScape Dashboard ===\n"
            "Mood: Happy\n"
            "Traits: brave: 10, kind: 5\n"
            "Timeline:\n"
            "- (empty)\n"
            "Events:\n"
            "- (empty)\n"
            "=========================="
        )

        result = render_dashboard_content(mock_game_instance)
        self.assertEqual(result, expected_output)

    def test_render_dashboard_content_no_llm_character(self):
        mock_player = Mock(name="Player", x=10, y=20)
        mock_player.name = "Player"

        mock_entities_values = Mock(return_value=[mock_player])
        mock_entities = Mock(values=mock_entities_values)
        mock_game_state_returned = Mock(player=mock_player, entities=mock_entities)

        mock_state_manager = Mock(
            get_game_state=Mock(return_value=mock_game_state_returned)
        )

        mock_game_instance = Mock(
            state_manager=mock_state_manager,
            timeline_log=[],
            event_log=[],
        )

        expected_output = (
            "=== DevScape Dashboard ===\n"
            "Player: Player at (10, 20)\n"
            "No companion present.\n"
            "Timeline:\n"
            "- (empty)\n"
            "Events:\n"
            "- (empty)\n"
            "=========================="
        )

        result = render_dashboard_content(mock_game_instance)
        self.assertEqual(result, expected_output)

    def test_render_dashboard_content_no_logs(self):
        mock_player = Mock(name="Player", x=10, y=20)
        mock_player.name = "Player"
        mock_llm_character = Mock(
            spec=LLMCharacter, mood="Happy", traits={"brave": 10, "kind": 5}
        )
        mock_llm_character.entity_type = constants.ENTITY_TYPES["NPC"]

        mock_entities_values = Mock(return_value=[mock_player, mock_llm_character])
        mock_entities = Mock(values=mock_entities_values)
        mock_game_state_returned = Mock(player=mock_player, entities=mock_entities)

        mock_state_manager = Mock(
            get_game_state=Mock(return_value=mock_game_state_returned)
        )

        mock_game_instance = Mock(
            state_manager=mock_state_manager,
            timeline_log=[],
            event_log=[],
        )

        expected_output = (
            "=== DevScape Dashboard ===\n"
            "Player: Player at (10, 20)\n"
            "Mood: Happy\n"
            "Traits: brave: 10, kind: 5\n"
            "Timeline:\n"
            "- (empty)\n"
            "Events:\n"
            "- (empty)\n"
            "=========================="
        )

        result = render_dashboard_content(mock_game_instance)
        self.assertEqual(result, expected_output)
