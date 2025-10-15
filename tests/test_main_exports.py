import importlib
import json
import sys
from types import SimpleNamespace

import pytest

from devscape import ollama_ai as ollama_ai_mod
from devscape.main import Game


@pytest.fixture(autouse=True)
def mock_game_dependencies(monkeypatch):
    mock_pygame = SimpleNamespace()
    mock_pygame.init = lambda *a, **k: None
    mock_pygame.font = SimpleNamespace(
        init=lambda *a, **k: None,
        Font=lambda *a, **k: SimpleNamespace(render=lambda *a, **k: None),
    )
    mock_pygame.display = SimpleNamespace(
        set_mode=lambda *a, **k: SimpleNamespace(), set_caption=lambda *a, **k: None
    )
    mock_pygame.time = SimpleNamespace(
        Clock=lambda *a, **k: SimpleNamespace(tick=lambda x: 0)
    )
    mock_pygame.event = SimpleNamespace(get=lambda *a, **k: [])
    monkeypatch.setitem(sys.modules, "pygame", mock_pygame)

    # Mock other heavy dependencies of game.main
    mod = importlib.import_module("devscape.main")
    llm_char = SimpleNamespace(
        id="llm_1", name="LLM", x=0, y=0, art=[], mood="neutral", traits={}
    )
    game_state = SimpleNamespace(
        player=SimpleNamespace(x=0, y=0, name="Player"),
        llm_character=llm_char,
        entities={"llm_1": llm_char},
    )
    monkeypatch.setattr(
        mod,
        "StateManager",
        lambda *a, **k: SimpleNamespace(
            game_state=game_state,
            get_game_state=lambda: game_state,
        ),
    )
    monkeypatch.setattr(
        ollama_ai_mod, "OllamaClient", lambda *a, **k: "ollama-client-stub"
    )
    monkeypatch.setattr(mod, "draw_chat_bubble", lambda *a, **k: None)
    monkeypatch.setattr(mod, "render_dashboard_content", lambda *a, **k: None)

    monkeypatch.setattr(mod, "render_pixel_art", lambda *a, **k: None)


def test_export_constellation_empty_logs():
    game = Game()
    game.llm_character_id = "llm_1"
    game.state_manager.get_game_state().entities["llm_1"].traits = {}

    result = game.export_constellation()
    data = json.loads(result)

    assert "events" in data
    assert data["events"] == []
    assert "glyphs" in data
    assert data["glyphs"] == []
    assert "lineage" in data
    assert data["lineage"].startswith("Version 0")


def test_export_constellation_with_events():
    game = Game()
    game.event_log = [
        {"timestamp": 1, "event": "storm", "mood": "anxious", "traits": {"courage": 4}},
        {"timestamp": 2, "event": "eclipse", "mood": "calm", "traits": {"focus": 3}},
    ]
    game.timeline_log = []
    game.llm_character_id = "llm_1"
    game.state_manager.get_game_state().entities["llm_1"].traits = {}

    result = game.export_constellation()
    data = json.loads(result)

    assert len(data["events"]) == 2
    assert data["events"][0]["event"] == "storm"
    assert data["events"][1]["event"] == "eclipse"
    assert len(data["glyphs"]) == 2
    assert data["glyphs"][0] == "⚡"  # anxious glyph
    assert data["glyphs"][1] == "☽"  # calm glyph
    assert data["lineage"].startswith("Version 0")
