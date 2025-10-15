from unittest import mock

from devscape.main import Game


def test_handle_text_input_chat_mode(mock_state_manager):
    with mock.patch("devscape.main.pygame") as _:
        with mock.patch("devscape.main.StateManager", return_value=mock_state_manager):
            game = Game()
            mock_state_manager.get_game_state.return_value.in_chat_mode = True
            mock_state_manager.get_game_state.return_value.chat_buffer = ""
            game.handle_text_input("hello")
    assert game.state_manager.get_game_state.return_value.chat_buffer == "hello"


def test_handle_text_input_not_chat_mode(mock_state_manager):
    with mock.patch("devscape.main.pygame") as _:
        with mock.patch("devscape.main.StateManager", return_value=mock_state_manager):
            game = Game()
            mock_state_manager.get_game_state.return_value.in_chat_mode = False
            mock_state_manager.get_game_state.return_value.chat_buffer = ""
            game.handle_text_input("hello")
    assert game.state_manager.get_game_state.return_value.chat_buffer == ""


def test_game_initialization(mock_state_manager):
    with mock.patch("devscape.main.pygame") as _:
        with mock.patch("devscape.main.StateManager", return_value=mock_state_manager):
            game = Game()
            _.init.assert_called_once()
            _.font.init.assert_called_once()
            _.display.set_mode.assert_called_once_with((800, 600))
            _.display.set_caption.assert_called_once_with("RuneScape-like Pixel Game")
            assert isinstance(game.state_manager, mock_state_manager.__class__)
            assert game.running is True


def test_handle_events_player_movement(mock_state_manager):
    with mock.patch("devscape.main.pygame") as _:
        with mock.patch("devscape.main.StateManager", return_value=mock_state_manager):
            game = Game()
            game.state_manager.get_game_state.return_value.in_chat_mode = False

            # Simulate K_UP event
            event_up = mock.MagicMock()
            event_up.type = _.KEYDOWN
            event_up.key = _.K_UP
            with mock.patch("devscape.main.pygame.event.get", return_value=[event_up]):
                game.handle_events()
                mock_state_manager.player_manager.move_player.assert_called_with(0, -1)

            # Simulate K_DOWN event
            event_down = mock.MagicMock()
            event_down.type = _.KEYDOWN
            event_down.key = _.K_DOWN
            with mock.patch(
                "devscape.main.pygame.event.get", return_value=[event_down]
            ):
                game.handle_events()
                mock_state_manager.player_manager.move_player.assert_called_with(0, 1)

            # Simulate K_LEFT event
            event_left = mock.MagicMock()
            event_left.type = _.KEYDOWN
            event_left.key = _.K_LEFT
            with mock.patch(
                "devscape.main.pygame.event.get", return_value=[event_left]
            ):
                game.handle_events()
                mock_state_manager.player_manager.move_player.assert_called_with(-1, 0)

            # Simulate K_RIGHT event
            event_right = mock.MagicMock()
            event_right.type = _.KEYDOWN
            event_right.key = _.K_RIGHT
            with mock.patch(
                "devscape.main.pygame.event.get", return_value=[event_right]
            ):
                game.handle_events()
                mock_state_manager.player_manager.move_player.assert_called_with(1, 0)


def test_show_chat_bubble_and_expire(mock_state_manager):
    with mock.patch("devscape.main.pygame") as _:
        _.time.get_ticks.return_value = 10000
        with mock.patch("devscape.main.StateManager", return_value=mock_state_manager):
            game = Game()
            mock_entity = mock.MagicMock()
            mock_entity.bubble_text = ""
            mock_entity.bubble_expires = 0
            game.entities = [mock_entity]

            # Test show_chat_bubble
            game.show_chat_bubble(mock_entity, "Hello", 1000)
            assert mock_entity.bubble_text == "Hello"
            assert mock_entity.bubble_duration == 1000
            assert mock_entity.bubble_expires > _.time.get_ticks()

            # Test _expire_chat_bubbles
            with mock.patch.object(
                _.time, "get_ticks", return_value=mock_entity.bubble_expires + 1
            ):
                game._expire_chat_bubbles(_.time.get_ticks())
                assert mock_entity.bubble_text == ""
                assert mock_entity.bubble_expires == 0


def test_send_player_message_success(mock_state_manager):
    with mock.patch("devscape.main.pygame") as _:
        with mock.patch("devscape.main.StateManager", return_value=mock_state_manager):
            game = Game()
            game.llm_character_id = "llm_char_1"
            mock_llm_character = mock.MagicMock()
            mock_llm_character.id = "llm_char_1"
            game.state_manager.get_game_state.return_value.entities.get.return_value = (
                mock_llm_character
            )

            with mock.patch.object(
                game.ollama_client, "send_message", return_value="AI Reply"
            ) as mock_send_message:
                with mock.patch.object(
                    game, "show_chat_bubble"
                ) as mock_show_chat_bubble:
                    game.send_player_message("Player Message")

                    mock_send_message.assert_called_once_with("Player Message")
                    assert mock_show_chat_bubble.call_count == 2
                    mock_show_chat_bubble.assert_any_call(game.player, "Player Message")
                    mock_show_chat_bubble.assert_any_call(
                        mock_llm_character, "AI Reply"
                    )
