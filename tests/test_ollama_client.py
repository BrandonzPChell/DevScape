import unittest
from unittest.mock import patch

from src.devscape.ollama_ai import OllamaClient, send_player_message_to_llm


class TestOllamaClient(unittest.TestCase):
    def setUp(self):
        self.client = OllamaClient()

    @patch("src.devscape.ollama_ai.OllamaClient._send_request")
    def test_get_move_and_dialogue(self, mock_send_request):
        mock_send_request.return_value = {
            "move": {"dx": 1, "dy": 0},
            "dialogue": "Hello",
            "raw": "MOVE: [1,0] | SAY: Hello",
        }

        game_map = ["S.E"]
        move, dialogue = self.client.get_move_and_dialogue(0, 0, 1, 0, game_map)

        self.assertEqual(move, (1, 0))
        self.assertEqual(dialogue, "Hello")
        mock_send_request.assert_called_once()

    @patch("src.devscape.ollama_ai.OllamaClient._send_request")
    def test_send_message(self, mock_send_request):
        mock_send_request.return_value = {
            "move": None,
            "dialogue": "AI response",
            "raw": "AI response",
        }

        response = self.client.send_message("User message")

        self.assertEqual(
            response, {"move": None, "dialogue": "AI response", "raw": "AI response"}
        )
        mock_send_request.assert_called_once()
        self.assertEqual(self.client.message_history[-2]["role"], "user")
        self.assertEqual(self.client.message_history[-2]["content"], "User message")
        self.assertEqual(self.client.message_history[-1]["role"], "assistant")

    @patch("src.devscape.ollama_ai.ollama_client.send_message")
    def test_send_player_message_to_llm(self, mock_send_message):
        send_player_message_to_llm("test message")
        mock_send_message.assert_called_once_with("test message")


if __name__ == "__main__":
    unittest.main()
