import importlib
import json
from unittest import mock

import pytest

from devscape import state


def to_json_str(data):
    return json.dumps(data, indent=2)


@pytest.fixture(autouse=True)
def reload_devscape_state():
    """Ensures devscape.state module is reloaded before each test."""
    importlib.reload(state)


@pytest.fixture
def mock_pygame_init():
    """Mocks pygame.init and pygame.display.set_mode to prevent actual pygame initialization."""
    with (
        mock.patch("pygame.init") as mock_init,
        mock.patch("pygame.display.set_mode") as mock_set_mode,
    ):
        yield mock_init, mock_set_mode


@pytest.fixture
def mock_state_manager():
    """Mocks the StateManager class and its get_game_state method."""
    with mock.patch("devscape.state_manager.StateManager") as MockStateManager:
        mock_instance = MockStateManager.return_value
        mock_game_state = mock.Mock()
        mock_game_state.in_chat_mode = False  # Default value
        mock_game_state.chat_buffer = ""  # Default value
        mock_instance.get_game_state.return_value = mock_game_state
        yield mock_instance
