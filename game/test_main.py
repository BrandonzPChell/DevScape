import json
import unittest
from unittest.mock import MagicMock, patch

import pygame

from game.main import Game
from game.state import Entity, LLMCharacter
from game import constants # Import constants here

# Mock constants and maps to avoid pygame initialization issues in tests
with patch('game.constants.SCREEN_WIDTH', 800), \
     patch('game.constants.SCREEN_HEIGHT', 600), \
     patch('game.constants.TILE_SIZE', 16), \
     patch('game.maps.GAME_MAP', [['.', '.']]), \
     patch('game.maps.MOOD_GLYPHS', {}):
    class TestGame(unittest.TestCase):

        def setUp(self):
            # Define all patchers here
            self.patcher_pygame_init = patch('pygame.init')
            self.patcher_pygame_font_init = patch('pygame.font.init')
            self.patcher_pygame_display_set_mode = patch('pygame.display.set_mode')
            self.patcher_pygame_display_set_caption = patch('pygame.display.set_caption')
            self.patcher_pygame_time_clock = patch('pygame.time.Clock')
            self.patcher_pygame_font_font = patch('pygame.font.Font')
            self.patcher_ollama_get_move_and_dialogue = patch('game.main.get_llm_move')

            # Start them and assign to instance vars
            self.mock_pygame_init = self.patcher_pygame_init.start()
            self.mock_pygame_font_init = self.patcher_pygame_font_init.start()
            self.mock_pygame_display_set_mode = self.patcher_pygame_display_set_mode.start()
            self.mock_pygame_display_set_caption = self.patcher_pygame_display_set_caption.start()
            self.mock_pygame_time_clock = self.patcher_pygame_time_clock.start()
            self.mock_pygame_font_font = self.patcher_pygame_font_font.start()
            self.mock_get_llm_move = self.patcher_ollama_get_move_and_dialogue.start() # Renamed for clarity

            # Ensure cleanup after each test
            self.addCleanup(self.patcher_pygame_init.stop)
            self.addCleanup(self.patcher_pygame_font_init.stop)
            self.addCleanup(self.patcher_pygame_display_set_mode.stop)
            self.addCleanup(self.patcher_pygame_display_set_caption.stop)
            self.addCleanup(self.patcher_pygame_time_clock.stop)
            self.addCleanup(self.patcher_pygame_font_font.stop)
            self.addCleanup(self.patcher_ollama_get_move_and_dialogue.stop)

            self.game = Game()
            self.game.ollama_client = MagicMock() # Mock the ollama_client instance
            self.game.ollama_client.send_message.return_value = "Mocked AI response"

            # Set the return value for the patched get_llm_move
            self.mock_get_llm_move.return_value = ((0, 0), "Mocked LLM dialogue")
            self.game.llm_character = Entity("AI", 22, 15, []) # Correctly instantiate as Entity
            self.game.llm_character.mood = "neutral"
            self.game.llm_character.traits = {"patience": 10, "courage": 5, "focus": 5, "empathy": 5}
            self.game.timeline_log = []
            self.game.event_log = []
            self.game.llm_character.bubble_text = None


        def test_update_llm_move_with_dialogue(self):
            # Simulate a move and dialogue from LLM
            self.mock_get_llm_move.return_value = ((1, 0), "Hello there!")
            self.game.llm_move_interval = 1000 # Set a short interval for testing
            self.game.should_speak = True

            initial_llm_x = self.game.llm_character.x
            initial_llm_y = self.game.llm_character.y

            # First update, should trigger LLM move
            self.game.update(1000) # dt = 1000, llm_move_timer = 1000
            self.assertEqual(self.game.llm_character.x, initial_llm_x + 1)
            self.assertEqual(self.game.llm_character.y, initial_llm_y)
            self.assertEqual(self.game.llm_character.bubble_text, "Hello there!")
            self.mock_get_llm_move.assert_called_once()
            self.mock_get_llm_move.reset_mock()

            # Second update, should not trigger LLM move yet
            self.game.update(500) # dt = 500, llm_move_timer = 500
            self.assertEqual(self.game.llm_character.x, initial_llm_x + 1)
            self.assertEqual(self.game.llm_character.y, initial_llm_y)
            self.mock_get_llm_move.assert_not_called()

            # Third update, should trigger LLM move again
            self.mock_get_llm_move.return_value = ((0, 1), "Nice weather!")
            self.game.update(500) # dt = 500, llm_move_timer = 1000
            self.assertEqual(self.game.llm_character.x, initial_llm_x + 1)
            self.assertEqual(self.game.llm_character.y, initial_llm_y + 1)
            self.assertEqual(self.game.llm_character.bubble_text, "Nice weather!")
            self.mock_get_llm_move.assert_called_once()

        @patch('pygame.time.get_ticks', side_effect=[0, 1000, 2000, 3000, 4000])
        def test_update_llm_move_silent_indicator(self, mock_get_ticks):
            # Simulate no move and no dialogue, with should_speak = False
            self.mock_get_llm_move.return_value = ((0, 0), None)
            self.game.llm_move_interval = 1000
            self.game.should_speak = False

            initial_llm_x = self.game.llm_character.x
            initial_llm_y = self.game.llm_character.y

            self.game.update(1000)
            self.assertEqual(self.game.llm_character.x, initial_llm_x)
            self.assertEqual(self.game.llm_character.y, initial_llm_y)
            self.assertIn(self.game.llm_character.bubble_text, ["...", "zzz", "—", "♪"]) # Check for silent indicator
            self.mock_get_llm_move.assert_called_once()

        @patch('pygame.time.get_ticks', side_effect=[0, 1000, 2000, 3000, 4000])
        def test_update_llm_move_exception_handling(self, mock_get_ticks):
            # Simulate an exception during LLM move
            self.mock_get_llm_move.side_effect = Exception("LLM connection error")
            self.game.llm_move_interval = 1000
            self.game.should_speak = True # Should not show silent indicator if should_speak is True

            initial_llm_x = self.game.llm_character.x
            initial_llm_y = self.game.llm_character.y

            self.game.update(1000)
            self.assertEqual(self.game.llm_character.x, initial_llm_x)
            self.assertEqual(self.game.llm_character.y, initial_llm_y)
            self.assertIsNone(self.game.llm_character.bubble_text) # No bubble on error
            self.mock_get_llm_move.assert_called_once()

        @patch('pygame.time.get_ticks', side_effect=[0, 1000, 2000, 3000, 4000])
        def test_update_camera_clamping(self, mock_get_ticks):
            # Test clamping at top-left
            self.game.player.x = 0
            self.game.player.y = 0
            self.game.update(1000)
            self.assertEqual(self.game.camera_offset_x, 0)
            self.assertEqual(self.game.camera_offset_y, 0)

            # Test clamping at bottom-right (assuming a small map for simplicity)
            # Mock map dimensions to be smaller than screen for clamping to occur
            with patch('game.constants.SCREEN_WIDTH', 100), \
                 patch('game.constants.SCREEN_HEIGHT', 100), \
                 patch('game.constants.TILE_SIZE', 16), \
                 patch('game.maps.GAME_MAP', [list('...'), list('...'), list('...')]) as mock_game_map:
                # Reinitialize game AFTER patching GAME_MAP
                self.game = Game()
                # Explicitly set map dimensions based on the mocked GAME_MAP
                self.game.map_width_pixels = len(mock_game_map[0]) * constants.TILE_SIZE
                self.game.map_height_pixels = len(mock_game_map) * constants.TILE_SIZE
                self.game.update(1000)
                # Expected camera offset for a 3x3 map (48x48 pixels) on a 100x100 screen
                # SCREEN_WIDTH - map_width_pixels = 100 - 48 = 52
                # SCREEN_HEIGHT - map_height_pixels = 100 - 48 = 52
                # Player at (2,2) means player_x_pixel = 32, player_y_pixel = 32
                # camera_offset_x = 100//2 - 32 = 50 - 32 = 18
                # camera_offset_y = 100//2 - 32 = 50 - 32 = 18
                # Clamped: max(18, 52) = 52
                self.assertEqual(self.game.camera_offset_x, 52)
                self.assertEqual(self.game.camera_offset_y, 52)
        @patch('pygame.time.get_ticks', side_effect=[0, 1000, 2000, 3000, 4000, 5000, 6000, 7000])
        def test_update_trait_evolution(self, mock_get_ticks):
            self.game.llm_character.traits = {"patience": 10.0}
            self.game.planetary_mood = 0.5 # Positive mood, should increase patience

            initial_patience = self.game.llm_character.traits["patience"]
            self.game.update(1000) # dt = 1000ms = 1 second
            # base_evolution_rate = 0.1 per second
            # mood_factor = 1.0 + 0.5 = 1.5
            # change = 0.1 * 1 * 1.5 = 0.15
            expected_patience = initial_patience + 0.15
            self.assertAlmostEqual(self.game.llm_character.traits["patience"], expected_patience)

        def test_export_data(self):
            self.game.player.x = 1
            self.game.player.y = 2
            self.game.llm_character.x = 3
            self.game.llm_character.y = 4
            self.game.llm_character.mood = "happy"
            self.game.llm_character.traits = {"strength": 10, "speed": 5}
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
            self.assertEqual(data["event_log"][0]["action"], "move")
            self.assertIn("timestamp", data)
            self.assertIn("version", data)

        def test_export_data_no_llm_traits(self):
            del self.game.llm_character.traits # Remove traits attribute
            exported_json = self.game.export_data()
            data = json.loads(exported_json)
            self.assertEqual(data["traits"], {})

        def test_generate_sprite(self):
            self.assertEqual(self.game.generate_sprite(""), ["....", ".##.", ".##.", "...."])
            self.assertEqual(self.game.generate_sprite("seed"), ["XXXX", "X..X", "X..X", "XXXX"])
            self.assertEqual(self.game.generate_sprite("seeda"), ["O.O", ".O.", "O.O"])

        def test_export_lore(self):
            lore_json = self.game.export_lore()
            lore_data = json.loads(lore_json)
            self.assertIn("arc", lore_data)
            self.assertIn("glyphs", lore_data)
            self.assertIn("lineage", lore_data)

        def test_generate_overlay(self):
            self.assertEqual(self.game.generate_overlay("happy"), ["\\o/", "| |", "/ \\"])
            self.assertEqual(self.game.generate_overlay("angry"), ["X X", "---", "/_\\"])
            self.assertEqual(self.game.generate_overlay("neutral"), ["...", ". .", "..."])
            self.assertEqual(self.game.generate_overlay("unknown"), ["...", ". .", "..."])

        def test_update_planetary_mood(self):
            self.game.update_planetary_mood("serene")
            self.assertEqual(self.game.planetary_mood, 0.5)
            self.assertEqual(self.game.llm_character.mood, "serene")

            self.game.update_planetary_mood("chaotic")
            self.assertEqual(self.game.planetary_mood, -0.7)
            self.assertEqual(self.game.llm_character.mood, "chaotic")

            self.game.update_planetary_mood("unknown_mood")
            self.assertEqual(self.game.planetary_mood, 0.0)
            self.assertEqual(self.game.llm_character.mood, "neutral")

        def test_apply_planetary_event(self):
            initial_courage = self.game.llm_character.traits["courage"]
            initial_focus = self.game.llm_character.traits["focus"]
            initial_empathy = self.game.llm_character.traits["empathy"]

            self.game.apply_planetary_event("storm")
            self.assertEqual(self.game.planetary_mood, -0.3) # anxious
            self.assertEqual(self.game.llm_character.mood, "anxious")
            self.assertEqual(self.game.llm_character.traits["courage"], initial_courage - 1)
            self.assertEqual(len(self.game.event_log), 1)

            self.game.apply_planetary_event("eclipse")
            self.assertEqual(self.game.planetary_mood, 0.2) # calm
            self.assertEqual(self.game.llm_character.mood, "calm")
            self.assertEqual(self.game.llm_character.traits["focus"], initial_focus + 1)
            self.assertEqual(len(self.game.event_log), 2)

            self.game.apply_planetary_event("festival")
            self.assertEqual(self.game.planetary_mood, 0.7) # joyful
            self.assertEqual(self.game.llm_character.mood, "joyful")
            self.assertEqual(self.game.llm_character.traits["empathy"], initial_empathy + 1)
            self.assertEqual(len(self.game.event_log), 3)

            self.game.apply_planetary_event("unknown_event")
            self.assertEqual(self.game.planetary_mood, 0.0) # neutral
            self.assertEqual(self.game.llm_character.mood, "neutral")
            self.assertEqual(len(self.game.event_log), 4)

        def test_export_timeline(self):
            self.game.timeline_log = [{"timestamp": 1, "mood": "happy"}]
            timeline_json = self.game.export_timeline()
            timeline_data = json.loads(timeline_json)
            self.assertEqual(timeline_data[0]["mood"], "happy")

        def test_export_trait_chart(self):
            self.game.llm_character.traits = {"strength": 10}
            self.game.timeline_log = [{"timestamp": 100}]
            chart_json = self.game.export_trait_chart()
            chart_data = json.loads(chart_json)
            self.assertEqual(chart_data["traits"]["strength"], 10)
            self.assertEqual(chart_data["timestamp"], 100)
            self.assertEqual(chart_data["history_length"], 1)

        def test_export_constellation(self):
            self.game.event_log = [{"mood": "serene"}, {"mood": "chaotic"}]
            constellation_json = self.game.export_constellation()
            constellation_data = json.loads(constellation_json)
            self.assertEqual(constellation_data["glyphs"], ["✦", "☄"])
            self.assertIn("lineage", constellation_data)

        def test_export_events(self):
            self.game.event_log = [{"event": "test"}]
            events_json = self.game.export_events()
            events_data = json.loads(events_json)
            self.assertEqual(events_data[0]["event"], "test")

        @patch('builtins.open', new_callable=unittest.mock.mock_open)
        @patch('json.dumps', return_value="{{}}")
        def test_save_timeline(self, mock_json_dumps, mock_open):
            self.game.save_timeline("test_timeline.json")
            mock_open.assert_called_once_with("test_timeline.json", "w", encoding="utf-8")
            mock_open.return_value.write.assert_called_once_with("{{}}")

        @patch('builtins.open', new_callable=unittest.mock.mock_open)
        @patch('json.dumps', return_value="{{}}")
        def test_save_events(self, mock_json_dumps, mock_open):
            self.game.save_events("test_events.json")
            mock_open.assert_called_once_with("test_events.json", "w", encoding="utf-8")
            mock_open.return_value.write.assert_called_once_with("{{}}")

        @patch('builtins.open', new_callable=unittest.mock.mock_open)
        @patch('json.dumps', return_value="{{}}")
        def test_save_constellation(self, mock_json_dumps, mock_open):
            self.game.save_constellation("test_constellation.json")
            mock_open.assert_called_once_with("test_constellation.json", "w", encoding="utf-8")
            mock_open.return_value.write.assert_called_once_with("{{}}")

        def test_export_coverage_badge(self):
            badge_json = json.loads(self.game.export_coverage_badge(90))
            self.assertEqual(badge_json["color"], "brightgreen")
            self.assertIn("90%25-brightgreen", badge_json["markdown"])

            badge_json = json.loads(self.game.export_coverage_badge(75))
            self.assertEqual(badge_json["color"], "yellow")

            badge_json = json.loads(self.game.export_coverage_badge(55))
            self.assertEqual(badge_json["color"], "orange")

            badge_json = json.loads(self.game.export_coverage_badge(40))
            self.assertEqual(badge_json["color"], "red")

        def test_export_covenant_badge(self):
            badge_json = json.loads(self.game.export_covenant_badge(True, True))
            self.assertEqual(badge_json["status"], "passing")
            self.assertEqual(badge_json["color"], "brightgreen")

            badge_json = json.loads(self.game.export_covenant_badge(False, True))
            self.assertEqual(badge_json["status"], "failing")
            self.assertEqual(badge_json["color"], "red")

        def test_export_lineage_badge(self):
            self.game.timeline_log = []
            badge_json = json.loads(self.game.export_lineage_badge())
            self.assertEqual(badge_json["entries"], 0)
            self.assertEqual(badge_json["color"], "lightgrey")

            self.game.timeline_log = [{}, {}]
            badge_json = json.loads(self.game.export_lineage_badge())
            self.assertEqual(badge_json["entries"], 2)
            self.assertEqual(badge_json["color"], "blue")
