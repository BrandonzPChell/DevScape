import sys  # Moved to top-level
from types import SimpleNamespace

import pytest

import devscape.main as mod  # Assuming Game is also in main.py
from devscape.state import LLMCharacter


def _stub_game(monkeypatch):
    # monkeypatch pygame and StateManager quickly
    # import sys # Removed

    # Create a persistent game_state object
    game_state = SimpleNamespace(
        player=SimpleNamespace(x=0, y=0, name="P"),
        llm_character=LLMCharacter(
            id="llm_char_id",
            name="L",
            x=0,
            y=0,
            art=[],
            mood="neutral",
            traits={"courage": 0, "focus": 0, "empathy": 0},
            sight_range=3,
        ),
        entities={
            "llm_char_id": LLMCharacter(
                id="llm_char_id",
                name="L",
                x=0,
                y=0,
                art=[],
                mood="neutral",
                sight_range=3,
            )
        },
    )

    fake_pg = SimpleNamespace(
        init=lambda *a, **k: None,
        display=SimpleNamespace(set_mode=lambda *a, **k: SimpleNamespace()),
    )
    monkeypatch.setitem(sys.modules, "pygame", fake_pg)
    monkeypatch.setattr(
        mod,
        "StateManager",
        lambda *a, **k: SimpleNamespace(
            game_state=game_state,
            get_game_state=lambda: game_state,
        ),
    )
    for fn in ("draw_chat_bubble", "render_dashboard_content", "render_pixel_art"):
        if hasattr(mod, fn):
            monkeypatch.setattr(mod, fn, lambda *a, **k: None)
    return mod.Game()


def test_apply_planetary_event_variants(monkeypatch):
    if not hasattr(mod, "Game") or not hasattr(mod.Game(), "apply_planetary_event"):
        pytest.skip("Game.apply_planetary_event not present")
    game_instance = _stub_game(monkeypatch)
    # craft a few example planetary events to exercise branches
    examples = [
        {"type": "storm", "mood": "anxious", "trait_changes": {"courage": -1}},
        {"type": "eclipse", "mood": "calm", "trait_changes": {"focus": 1}},
        {"type": "festival", "mood": "joyful", "trait_changes": {"empathy": 1}},
        {"type": "unknown_event", "mood": "neutral", "trait_changes": {}},
    ]

    # Initialize traits for llm_character
    game_instance.state_manager.get_game_state().entities["llm_char_id"].traits = {
        "courage": 0,
        "focus": 0,
        "empathy": 0,
    }
    for ev in examples:
        event_type = ev["type"]
        expected_mood = ev["mood"]
        expected_trait_changes = ev["trait_changes"]

        initial_traits = (
            game_instance.state_manager.get_game_state()
            .entities["llm_char_id"]
            .traits.copy()
        )
        game_instance.apply_planetary_event(event_type)

        current_llm_char = game_instance.state_manager.get_game_state().entities[
            "llm_char_id"
        ]
        assert current_llm_char.mood == expected_mood
        for trait, change in expected_trait_changes.items():
            assert (
                current_llm_char.traits[trait] == initial_traits.get(trait, 0) + change
            )
        assert any(entry["event"] == event_type for entry in game_instance.event_log)
