from unittest import mock

from src.devscape.main import Game


def test_handle_text_input_chat_mode(mock_pygame_init, mock_state_manager):
    with mock.patch("src.devscape.main.StateManager", return_value=mock_state_manager):
        game = Game()
        mock_state_manager.get_game_state.return_value.in_chat_mode = True
        mock_state_manager.get_game_state.return_value.chat_buffer = ""
        game.handle_text_input("hello")
    assert game.state_manager.get_game_state.return_value.chat_buffer == "hello"


def test_handle_text_input_not_chat_mode(mock_pygame_init, mock_state_manager):
    with mock.patch("src.devscape.main.StateManager", return_value=mock_state_manager):
        game = Game()
        mock_state_manager.get_game_state.return_value.in_chat_mode = False
        mock_state_manager.get_game_state.return_value.chat_buffer = ""
        game.handle_text_input("hello")
    assert game.state_manager.get_game_state.return_value.chat_buffer == ""
