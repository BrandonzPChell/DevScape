import unittest
from unittest.mock import MagicMock, patch

from devscape.player_progression import check_level_up, update_quests
from devscape.state import GameState, Player, Quest


class TestPlayerProgression(unittest.TestCase):
    def setUp(self):
        self.mock_game_state = MagicMock(spec=GameState)
        self.mock_player = MagicMock(spec=Player)
        self.mock_game_state.player = self.mock_player
        self.mock_game_state.message = ""

    def test_check_level_up_no_level_up(self):
        """Player should not level up if XP is below the threshold."""
        self.mock_player.level = 1
        self.mock_player.xp = 50
        with patch("devscape.player_progression.LEVEL_UP_THRESHOLDS", {1: 100}):
            check_level_up(self.mock_game_state, self.mock_player)
        self.assertEqual(self.mock_player.level, 1)

    def test_check_level_up_single_level_up(self):
        """Player should level up once if XP meets the threshold."""
        self.mock_player.level = 1
        self.mock_player.xp = 100
        self.mock_player.max_health = 100
        self.mock_player.sight_range = 5
        with patch("devscape.player_progression.LEVEL_UP_THRESHOLDS", {1: 100, 2: 200}):
            check_level_up(self.mock_game_state, self.mock_player)
        self.assertEqual(self.mock_player.level, 2)
        self.assertEqual(self.mock_player.max_health, 120)
        self.assertEqual(self.mock_player.health, 120)
        self.assertEqual(self.mock_player.sight_range, 6)
        self.assertIn("Congratulations! You reached Level 2!", self.mock_game_state.message)

    def test_check_level_up_multiple_level_ups(self):
        """Player should level up multiple times if XP is high enough."""
        self.mock_player.level = 1
        self.mock_player.xp = 300
        self.mock_player.max_health = 100
        self.mock_player.sight_range = 5
        with patch("devscape.player_progression.LEVEL_UP_THRESHOLDS", {1: 100, 2: 200, 3: 300}):
            check_level_up(self.mock_game_state, self.mock_player)
        self.assertEqual(self.mock_player.level, 4)
        self.assertEqual(self.mock_player.max_health, 160)
        self.assertEqual(self.mock_player.health, 160)
        self.assertEqual(self.mock_player.sight_range, 8)

    def test_update_quests_no_match(self):
        """Quest progress should not update if entity type does not match."""
        mock_quest = MagicMock(spec=Quest)
        mock_quest.completed = False
        mock_quest.type = "ENEMY"
        mock_quest.current_progress = 0
        self.mock_game_state.quests = [mock_quest]
        mock_callback = MagicMock()

        update_quests(self.mock_game_state, "RESOURCE", mock_callback)
        self.assertEqual(mock_quest.current_progress, 0)
        mock_callback.assert_not_called()

    def test_update_quests_match_and_progress(self):
        """Quest progress should update if entity type matches."""
        mock_quest = MagicMock(spec=Quest)
        mock_quest.completed = False
        mock_quest.type = "ENEMY"
        mock_quest.current_progress = 0
        mock_quest.target_count = 2
        self.mock_game_state.quests = [mock_quest]
        mock_callback = MagicMock()

        update_quests(self.mock_game_state, "ENEMY", mock_callback)
        self.assertEqual(mock_quest.current_progress, 1)
        self.assertFalse(mock_quest.completed)
        mock_callback.assert_not_called()

    def test_update_quests_completion(self):
        """Quest should be completed and callback called when progress reaches target."""
        mock_quest = MagicMock(spec=Quest)
        mock_quest.completed = False
        mock_quest.type = "ENEMY"
        mock_quest.current_progress = 1
        mock_quest.target_count = 2
        self.mock_game_state.quests = [mock_quest]
        mock_callback = MagicMock()

        update_quests(self.mock_game_state, "ENEMY", mock_callback)
        self.assertEqual(mock_quest.current_progress, 2)
        self.assertTrue(mock_quest.completed)
        mock_callback.assert_called_once_with(mock_quest)

if __name__ == "__main__":
    unittest.main()
