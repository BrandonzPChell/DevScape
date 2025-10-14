import importlib
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def stub_game_environment(monkeypatch):
    # Minimal pygame stub so imports succeed
    fake_pg = SimpleNamespace()
    fake_pg.init = lambda *a, **k: None
    fake_pg.display = SimpleNamespace(
        set_mode=lambda *a, **k: SimpleNamespace(), set_caption=lambda *a, **k: None
    )
    fake_pg.font = SimpleNamespace(
        init=lambda *a, **k: None,
        Font=lambda *a, **k: SimpleNamespace(render=lambda *a, **k: None),
    )
    fake_pg.time = SimpleNamespace(
        Clock=lambda *a, **k: SimpleNamespace(tick=lambda x: 0), get_ticks=lambda: 0
    )
    fake_pg.event = SimpleNamespace(get=lambda *a, **k: [])
    monkeypatch.setitem(sys.modules, "pygame", fake_pg)

    mod = importlib.import_module("devscape.main")

    # Stub heavy deps used by Game
    if hasattr(mod, "StateManager"):
        mock_llm_char = SimpleNamespace(
            id="llm_char_1",
            x=0,
            y=0,
            name="LLM",
            mood="neutral",
            traits={},
            bubble_text="",
            bubble_start_time=0,
            bubble_duration=0,
            bubble_expires=0,
        )
        mock_game_state = SimpleNamespace(
            player=SimpleNamespace(x=0, y=0, name="Player"),
            entities={"llm_char_1": mock_llm_char},
        )
        monkeypatch.setattr(
            mod,
            "StateManager",
            lambda *a, **k: SimpleNamespace(
                game_state=mock_game_state,
                get_game_state=lambda: mock_game_state,
                get_all_entities=lambda: {"llm_char_1": mock_llm_char},
            ),
        )
    for fn in ("draw_chat_bubble", "render_dashboard_content", "render_pixel_art"):
        if hasattr(mod, fn):
            monkeypatch.setattr(mod, fn, lambda *a, **k: None)


def _set_chat_bubble(entity, text="hi", current_ticks=0, duration=1000):
    entity.bubble_text = text
    entity.bubble_start_time = current_ticks
    entity.bubble_duration = duration
    entity.bubble_expires = current_ticks + duration
    return entity


def test_chat_bubble_expiry(monkeypatch):
    mod = importlib.import_module("devscape.main")
    if not hasattr(mod, "Game"):
        pytest.skip("Game class missing in game.main")
    game_instance = mod.Game()

    # Mock pygame.time.get_ticks to control time
    current_ticks = 1000  # Start at 1 second
    monkeypatch.setattr(mod.pygame.time, "get_ticks", lambda: current_ticks)

    # Create a mock entity and add it to game.entities
    llm_char = game_instance.state_manager.get_game_state().entities["llm_char_1"]

    # Set a chat bubble that should expire
    _set_chat_bubble(
        llm_char, text="stale", current_ticks=current_ticks - 2000, duration=1000
    )  # Expires 1 second before current_ticks

    # Call update with dt=0 to trigger expiry logic
    try:
        game_instance.update(0)
    except TypeError:
        game_instance.update()

    # After update, stale bubble should be cleared
    assert llm_char.bubble_text == ""
    assert llm_char.bubble_start_time == 0
    assert llm_char.bubble_duration == 0
    assert llm_char.bubble_expires == 0


def test_llm_chat_and_silent_indicators(monkeypatch):
    mod = importlib.import_module("devscape.main")
    if not hasattr(mod, "Game"):
        pytest.skip("Game class missing in game.main")
    game_instance = mod.Game()
    game_instance.llm_character_id = (
        "llm_char_1"  # Explicitly set llm_character_id for the test
    )

    # Mock pygame.time.get_ticks to control time
    current_ticks = 1000  # Start at 1 second
    monkeypatch.setattr(mod.pygame.time, "get_ticks", lambda: current_ticks)

    # Mock get_llm_move to return no movement and no dialogue
    monkeypatch.setattr(mod, "get_llm_move", lambda *a, **k: ((0, 0), None))

    # Mock show_chat_bubble to capture calls
    show_chat_bubble_calls = []
    monkeypatch.setattr(
        game_instance,
        "show_chat_bubble",
        lambda entity, text, duration=3000: show_chat_bubble_calls.append(
            (entity, text, duration)
        ),
    )

    # Case A: should_speak is False, move_delta is (0,0) -> silent indicator
    game_instance.should_speak = False
    game_instance.state_manager.get_game_state().entities["llm_char_1"].mood = "neutral"
    game_instance.llm_move_timer = (
        game_instance.llm_move_interval
    )  # Trigger LLM move logic
    try:
        game_instance.update(0)
    except TypeError:
        game_instance.update()
    assert len(show_chat_bubble_calls) == 1
    assert show_chat_bubble_calls[0][1] == "..."  # Neutral indicator
    show_chat_bubble_calls.clear()

    # Case B: should_speak is True, move_delta is (0,0), dialogue is None -> no silent indicator
    game_instance.should_speak = True
    game_instance.llm_move_timer = (
        game_instance.llm_move_interval
    )  # Trigger LLM move logic
    try:
        game_instance.update(0)
    except TypeError:
        game_instance.update()
    assert len(show_chat_bubble_calls) == 0  # No bubble should be shown

    # Case C: should_speak is True, move_delta is (0,0), dialogue is present -> show dialogue
    monkeypatch.setattr(mod, "get_llm_move", lambda *a, **k: ((0, 0), "Hello"))
    game_instance.should_speak = True
    game_instance.llm_move_timer = (
        game_instance.llm_move_interval
    )  # Trigger LLM move logic
    try:
        game_instance.update(0)
    except TypeError:
        game_instance.update()
    assert len(show_chat_bubble_calls) == 1
    assert show_chat_bubble_calls[0][1] == "Hello"
