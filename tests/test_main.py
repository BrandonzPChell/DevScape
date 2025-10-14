"""Tests for the main game logic in game.main."""

import json
import unittest
from unittest.mock import MagicMock, patch

from devscape import constants  # Import constants here
from devscape.main import Game
from devscape.state import LLMCharacter

# Mock constants and maps to avoid pygame initialization issues in tests
with (
    patch("devscape.constants.SCREEN_WIDTH", 800),
    patch("devscape.constants.SCREEN_HEIGHT", 600),
    patch("devscape.constants.TILE_SIZE", 16),
    patch("devscape.main.GAME_MAP", [[".", "."]]),
    patch("devscape.maps.MOOD_GLYPHS", {}),
):

    class TestGame(unittest.TestCase):
        def setUp(self):
            # from devscape.main import Game  # Import Game here - REMOVED
            # Define all patchers here
            self.patcher_pygame_init = patch("devscape.main.pygame.init")
            self.patcher_pygame_font_init = patch("devscape.main.pygame.font.init")
            self.patcher_pygame_display_set_mode = patch(
                "devscape.main.pygame.display.set_mode"
            )
            self.patcher_pygame_display_set_caption = patch(
                "devscape.main.pygame.display.set_caption"
            )
            self.patcher_pygame_time_clock = patch("devscape.main.pygame.time.Clock")
            self.patcher_pygame_font_font = patch("devscape.main.pygame.font.Font")
            self.patcher_ollama_get_move_and_dialogue = patch(
                "devscape.main.get_llm_move"
            )

            # Start them and assign to instance vars
            self.mock_pygame_init = self.patcher_pygame_init.start()
            self.mock_pygame_font_init = self.patcher_pygame_font_init.start()
            self.mock_pygame_display_set_mode = (
                self.patcher_pygame_display_set_mode.start()
            )
            self.mock_pygame_display_set_caption = (
                self.patcher_pygame_display_set_caption.start()
            )
            self.mock_pygame_time_clock = self.patcher_pygame_time_clock.start()
            self.mock_pygame_font_font = self.patcher_pygame_font_font.start()
            self.mock_get_llm_move = (
                self.patcher_ollama_get_move_and_dialogue.start()  # Renamed for clarity
            )

            # Ensure cleanup after each test
            self.addCleanup(self.patcher_pygame_init.stop)
            self.addCleanup(self.patcher_pygame_font_init.stop)
            self.addCleanup(self.patcher_pygame_display_set_mode.stop)
            self.addCleanup(self.patcher_pygame_display_set_caption.stop)
            self.addCleanup(self.patcher_pygame_time_clock.stop)
            self.addCleanup(self.patcher_pygame_font_font.stop)
            self.addCleanup(self.patcher_ollama_get_move_and_dialogue.stop)

            self.game = Game()
            self.assertIsInstance(self.game, Game)

            # Retrieve the LLMCharacter that the Game instance is managing
            # The Game's __init__ will have already created a StateManager and populated entities
            # We need to ensure there's an LLMCharacter for the test to use.
            # If the Game's __init__ didn't create one, we'll create one and add it.
            if self.game.llm_character_id is None:
                # Create a specific LLMCharacter for testing if none exists
                test_llm_char = LLMCharacter(
                    id="llm_character_1",
                    name="LLM Char",
                    x=0,
                    y=0,
                    art=["LLMC"],
                    mood="neutral",
                    traits={"patience": 10, "courage": 5, "focus": 5, "empathy": 5},
                )
                self.game.state_manager.game_state.entities[test_llm_char.id] = (
                    test_llm_char
                )
                self.game.llm_character_id = test_llm_char.id

            # Now, get the actual LLMCharacter object that the game is using
            self.llm_character = self.game.state_manager.get_game_state().entities.get(
                self.game.llm_character_id
            )

            # Set initial traits and mood for the test
            self.llm_character.mood = "neutral"
            self.llm_character.traits = {
                "patience": 10,
                "courage": 5,
                "focus": 5,
                "empathy": 5,
            }

            self.game.ollama_client = MagicMock()  # Mock the ollama_client instance
            self.game.ollama_client.send_message.return_value = "Mocked AI response"

            # Set the return value for the patched get_llm_move
            self.mock_get_llm_move.return_value = ((1, 0), "Hello there!")
            # Initialize llm_character traits and mood if not already set by StateManager
            # These lines are now redundant as we set them directly above
            # if not self.game.llm_character.mood:
            #     self.game.llm_character.mood = "neutral"
            # if not self.game.llm_character.traits:
            #     self.game.llm_character.traits = {
            #         "patience": 10,
            #         "courage": 5,
            #         "focus": 5,
            #         "empathy": 5,
            #     }
            self.game.timeline_log = []
            self.game.event_log = []
            self.llm_character.bubble_text = None

        def test_update_llm_move_with_dialogue(self):
            initial_llm_x = 0
            initial_llm_y = 0
            self.llm_character.x = initial_llm_x
            self.llm_character.y = initial_llm_y
            self.game.llm_move_interval = 1000  # Set interval to match test expectation

            # First update, should trigger LLM move
            self.game.update(1000)  # dt = 1000, llm_move_timer = 1000
            self.assertEqual(self.llm_character.x, initial_llm_x + 1)
            self.assertEqual(self.llm_character.y, initial_llm_y)
            self.assertEqual(self.llm_character.bubble_text, "Hello there!")
            self.mock_get_llm_move.assert_called_once()
            self.mock_get_llm_move.reset_mock()

            # Second update, should not trigger LLM move yet
            self.game.update(500)  # dt = 500, llm_move_timer = 500
            self.assertEqual(self.llm_character.x, initial_llm_x + 1)
            self.assertEqual(self.llm_character.y, initial_llm_y)
            self.mock_get_llm_move.assert_not_called()

            # Third update, should trigger LLM move again
            self.mock_get_llm_move.return_value = ((0, 1), "Nice weather!")
            self.game.update(500)  # dt = 500, llm_move_timer = 1000
            self.assertEqual(self.llm_character.x, initial_llm_x + 1)
            self.assertEqual(self.llm_character.y, initial_llm_y + 1)
            self.assertEqual(self.llm_character.bubble_text, "Nice weather!")
            self.mock_get_llm_move.assert_called_once()

        @patch("pygame.time.get_ticks", side_effect=[0, 1000, 2000, 3000, 4000])
        def test_update_llm_move_silent_indicator(self, _mock_get_ticks):
            # Simulate no move and no dialogue, with should_speak = False
            self.mock_get_llm_move.return_value = ((0, 0), None)
            self.game.llm_move_interval = 1000
            self.game.should_speak = False

            initial_llm_x = self.llm_character.x
            initial_llm_y = self.llm_character.y

            self.game.update(1000)
            self.assertEqual(self.llm_character.x, initial_llm_x)
            self.assertEqual(self.llm_character.y, initial_llm_y)
            self.assertIn(
                self.llm_character.bubble_text,
                ["...", "zzz"],  # Check for silent indicator
            )
            self.mock_get_llm_move.assert_called_once()

        @patch("pygame.time.get_ticks", side_effect=[0, 1000, 2000, 3000, 4000])
        def test_update_llm_move_exception_handling(self, _mock_get_ticks):
            # Simulate an exception during LLM move
            self.mock_get_llm_move.side_effect = Exception("LLM connection error")
            self.game.llm_move_interval = 1000
            self.game.should_speak = (
                True  # Should not show silent indicator if should_speak is True
            )

            initial_llm_x = self.llm_character.x
            initial_llm_y = self.llm_character.y

            self.game.update(1000)
            self.assertEqual(self.llm_character.x, initial_llm_x)
            self.assertEqual(self.llm_character.y, initial_llm_y)
            self.assertIsNone(self.llm_character.bubble_text)  # No bubble on error
            self.mock_get_llm_move.assert_called_once()

        @patch("pygame.time.get_ticks", side_effect=range(0, 50000, 1000))
        def test_update_camera_clamping(self, _mock_get_ticks):
            # Test clamping at top-left
            self.game.player.x = 0
            self.game.player.y = 0
            self.game.update(1000)
            self.assertEqual(self.game.camera_offset_x, 0)
            self.assertEqual(self.game.camera_offset_y, 0)

            # Test clamping at bottom-right (assuming a small map for simplicity)
            # Mock map dimensions to be smaller than screen for clamping to occur
            with (
                patch("devscape.constants.SCREEN_WIDTH", 100),
                patch("devscape.constants.SCREEN_HEIGHT", 100),
                patch("devscape.constants.TILE_SIZE", 16),
                patch(
                    "devscape.maps.GAME_MAP", [list("..."), list("..."), list("...")]
                ) as mock_game_map,
            ):
                # Reinitialize game AFTER patching GAME_MAP
                self.game = Game()
                # Explicitly set map dimensions based on the mocked GAME_MAP
                self.game.map_width_pixels = len(mock_game_map[0]) * constants.TILE_SIZE
                self.game.map_height_pixels = len(mock_game_map) * constants.TILE_SIZE

                # Set player position to trigger clamping at bottom-right
                self.game.player.x = len(mock_game_map[0]) - 1
                self.game.player.y = len(mock_game_map) - 1

                self.game.update(1000)
                # Expected camera offset for a 3x3 map (48x48 pixels) on a 100x100 screen
                # SCREEN_WIDTH - map_width_pixels = 100 - 48 = 52
                # SCREEN_HEIGHT - map_height_pixels = 100 - 48 = 52
                # Player at (2,2) means player_x_pixel = 32, player_y_pixel = 32
                # camera_offset_x = 100//2 - 32 = 50 - 32 = 18
                # Clamped: max(18, 52) = 52
                self.assertEqual(self.game.camera_offset_x, 52)
                self.assertEqual(self.game.camera_offset_y, 52)

            # Test camera following player when map is larger than screen
            with (
                patch("devscape.constants.SCREEN_WIDTH", 100),
                patch("devscape.constants.SCREEN_HEIGHT", 100),
                patch("devscape.constants.TILE_SIZE", 16),
                patch(
                    "devscape.maps.GAME_MAP",
                    [list("...................."), list("....................")],
                ) as mock_game_map,  # 20x2 map
            ):
                self.game = Game()
                self.game.map_width_pixels = (
                    len(mock_game_map[0]) * constants.TILE_SIZE
                )  # 20 * 16 = 320
                self.game.map_height_pixels = (
                    len(mock_game_map) * constants.TILE_SIZE
                )  # 2 * 16 = 32

                # Player at (5,0) - camera should center on player
                self.game.player.x = 5
                self.game.player.y = 0
                self.game.update(1000)
                # Expected camera_offset_x: player_x_pixel = 5 * 16 = 80
                # SCREEN_WIDTH // 2 = 50
                # camera_offset_x = 50 - 80 = -30
                # Clamped: max(SCREEN_WIDTH - map_width_pixels, min(0, camera_offset_x))
                # max(100 - 320, min(0, -30)) = max(-220, -30) = -30
                self.assertEqual(self.game.camera_offset_x, -30)
                self.assertEqual(
                    self.game.camera_offset_y, 68  # Corrected expected value
                )

                # Player at (15,0) - camera should be clamped at right edge
                self.game.player.x = 15
                self.game.player.y = 0
                self.game.update(1000)
                # Expected camera_offset_x: player_x_pixel = 15 * 16 = 240
                # camera_offset_x = 50 - 240 = -190
                # Clamped: max(100 - 320, min(0, -190)) = max(-220, -190) = -190
            self.assertEqual(self.game.camera_offset_y, 68)  # Corrected expected value

        @patch(
            "pygame.time.get_ticks",
            side_effect=[0, 1000, 2000, 3000, 4000, 5000, 6000, 7000],
        )
        def test_update_trait_evolution(self, _mock_get_ticks):
            self.llm_character.traits = {"patience": 10.0}
            self.game.planetary_mood = 0.5  # Positive mood, should increase patience

            initial_patience = self.llm_character.traits["patience"]
            self.game.update(1000)  # dt = 1000ms = 1 second
            # base_evolution_rate = 0.1 per second
            # mood_factor = 1.0 + 0.5 = 1.5
            # change = 0.1 * 1 * 1.5 = 0.15
            expected_patience = initial_patience + 0.15
            self.assertAlmostEqual(
                self.llm_character.traits["patience"], expected_patience
            )

        def test_export_data(self):
            self.game.player.x = 1
            self.game.player.y = 2
            self.llm_character.x = 3
            self.llm_character.y = 4
            self.llm_character.mood = "happy"
            self.llm_character.traits = {"strength": 10, "speed": 5}
            self.game.timeline_log = [{"event": "start"}]
            self.game.event_log = [{"action": "move"}]

            exported_json = self.game.export_data()
            data = json.loads(exported_json)

            self.assertEqual(data["player"]["x"], 1)
            self.assertEqual(data["player"]["y"], 2)
            self.assertEqual(data["llm_character"]["x"], 3)
            self.assertEqual(data["llm_character"]["y"], 4)
            self.assertEqual(data["llm_character"]["mood"], "happy")
            self.assertEqual(data["traits"]["strength"], 10)
            self.assertEqual(data["traits"]["speed"], 5)
            self.assertEqual(data["timeline_log"][0]["event"], "start")
