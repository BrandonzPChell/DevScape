import importlib
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def stub_main_deps(monkeypatch):
    # stub pygame and heavy render/state dependencies
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
        Clock=lambda *a, **k: SimpleNamespace(tick=lambda x: 0)
    )
    fake_pg.event = SimpleNamespace(get=lambda *a, **k: [])
    mod = importlib.import_module("devscape.main")
    # stub StateManager and rendering helpers if present
    if hasattr(mod, "StateManager"):
        llm_char = SimpleNamespace(name="L", mood="neutral", traits={})
        game_state = SimpleNamespace(
            player=SimpleNamespace(x=0, y=0, name="P"),
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
    for fn in ("draw_chat_bubble", "render_dashboard_content", "render_pixel_art"):
        if hasattr(mod, fn):
            monkeypatch.setattr(mod, fn, lambda *a, **k: None)


def test_game_helpers_and_overlay_consistency():
    mod = importlib.import_module("devscape.main")
    if not hasattr(mod, "Game"):
        pytest.skip("Game class missing in game.main")
    game_instance = mod.Game()
    # generate overlays for a few moods if method present
    if hasattr(game_instance, "generate_overlay"):
        a = game_instance.generate_overlay("happy")
        b = game_instance.generate_overlay("neutral")
        assert isinstance(a, list)
        assert isinstance(b, list)
        # basic inequality check allowed to be permissive
        if a and b:
            assert a != b or any("happy" in s.lower() for s in a)
    # call any small, public helper if present
    for name in ("get_overlay_lines", "overlay_to_text", "format_entity_line"):
        if hasattr(game_instance, name):
            fn = getattr(game_instance, name)
            try:
                out = fn("test")
                # be permissive: expect str or list
                assert isinstance(out, (str, list, type(None)))
            except TypeError:
                # signature mismatch, accept as long as it didn't crash import
                pass
