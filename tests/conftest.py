# conftest.py
import json

import pytest
from unittest.mock import MagicMock

from devscape.main import Game


class DummyOllamaClient:
    """Simple controllable stand-in for the real Ollama client."""

    def __init__(self, should_fail=False, response="ok"):
        self.should_fail = should_fail
        self.response = response
        self.calls = []

    def send_message(self, message):
        self.calls.append(("send_message", message))
        if self.should_fail:
            raise RuntimeError("Simulated Ollama failure")
        return self.response

    def get_llm_move(self, *args, **kwargs):
        self.calls.append(("get_llm_move", args, kwargs))
        if self.should_fail:
            raise RuntimeError("Simulated Ollama failure")
        return {"move": "noop", "dialogue": None}


@pytest.fixture
def mock_state_manager():
    mock_sm = MagicMock()
    mock_sm.game_state.player.x = 0
    mock_sm.game_state.player.y = 0
    mock_sm.game_state.player.id = "player_1"
    mock_sm.game_state.player.bubble_text = ""
    mock_sm.game_state.player.bubble_expires = 0
    mock_sm.game_state.entities.get.return_value = MagicMock(id="llm_char_1", x=1, y=1, bubble_text="", bubble_expires=0)
    mock_sm.get_game_state.return_value.in_chat_mode = False
    mock_sm.get_game_state.return_value.chat_buffer = ""
    mock_sm.get_all_entities.return_value = {"player_1": mock_sm.game_state.player, "llm_char_1": mock_sm.game_state.entities.get.return_value}
    return mock_sm


@pytest.fixture
def tmp_db(tmp_path):
    """Path for ephemeral database or persistence files used by tests."""
    db_path = tmp_path / "devscape_test.db"
    # Caller can create the file or let the system under test create it
    yield db_path
    # cleanup not required: tmp_path is ephemeral


@pytest.fixture
def sample_entities():
    """Small, deterministic set of entities for tests that need game entities."""
    return [
        {"id": "player", "type": "Player", "x": 0, "y": 0},
        {"id": "npc_1", "type": "NPC", "x": 5, "y": 5},
    ]


@pytest.fixture
def ollama_client():
    """Default non-failing dummy Ollama client."""
    return DummyOllamaClient(should_fail=False, response="ok")


@pytest.fixture
def failing_ollama_client():
    """Dummy Ollama client that raises to exercise error branches."""
    return DummyOllamaClient(should_fail=True)


@pytest.fixture
def deterministic_game(tmp_db, sample_entities, ollama_client):
    """
    Create a minimal Game instance with injected deterministic dependencies.
    Adjust construction arguments to match your Game signature.
    """
    g = Game(entities=sample_entities)
    # inject predictable persistence path if Game supports it
    try:
        # prefer explicit attribute if available
        g.persistence_path = str(tmp_db)
    except Exception:
        # fall back silently if Game does not expose such attribute
        pass
    # inject mocked LLM client
    g.ollama_client = ollama_client
    # make deterministic toggles explicit if available
    if hasattr(g, "should_speak"):
        g.should_speak = False
    yield g
    # attempt graceful teardown if Game exposes cleanup
    if hasattr(g, "close"):
        try:
            g.close()
        except Exception:
            pass


@pytest.fixture
def timeline_data():
    """A small timeline payload useful for export/load tests."""
    return [{"event": "start", "ts": 0}, {"event": "move", "ts": 1}]


@pytest.fixture
def write_json_file(tmp_path):
    """Helper to write JSON to a file and return the path."""

    def _write(obj, name="data.json"):
        p = tmp_path / name
        p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        return p

    return _write
