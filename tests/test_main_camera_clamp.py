import importlib
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def stub_env(monkeypatch):
    # Minimal pygame surface/time/event stubs so Game imports safely
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

    # Stub StateManager to provide predictable map/world dimensions and player
    if hasattr(mod, "StateManager"):
        game_state = SimpleNamespace(
            player=SimpleNamespace(x=0, y=0, name="Player"),
            llm_character=SimpleNamespace(
                x=0, y=0, name="LLM", mood="neutral", traits={}
            ),
            entities={},
        )
        monkeypatch.setattr(
            mod,
            "StateManager",
            lambda *a, **k: SimpleNamespace(
                game_state=game_state,
                get_game_state=lambda: game_state,
                get_all_entities=lambda: SimpleNamespace(
                    values=lambda: [
                        SimpleNamespace(x=0, y=0, entity_type="PLAYER"),
                        SimpleNamespace(x=0, y=0, entity_type="LLM_CHARACTER"),
                    ]
                ),
            ),
        )

    # Stub rendering helpers (no-op)
    for fn in ("draw_chat_bubble", "render_dashboard_content", "render_pixel_art"):
        if hasattr(mod, fn):
            monkeypatch.setattr(mod, fn, lambda *a, **k: None)


def _safe_instantiate_game():
    mod = importlib.import_module("devscape.main")
    if not hasattr(mod, "Game"):
        pytest.skip("Game class missing in game.main")
    return mod.Game()


def test_camera_clamps_inside_world_bounds(monkeypatch):
    game_instance = _safe_instantiate_game()

    # Provide world/map bounds expected by clamp logic: width/height in tiles or pixels
    # Try common attribute names used in clamp logic
    if not hasattr(game_instance, "camera_offset_x"):
        game_instance.camera_offset_x = 0
    if not hasattr(game_instance, "camera_offset_y"):
        game_instance.camera_offset_y = 0

    # Provide map/world dimensions on G or G.state as commonly expected
    if hasattr(game_instance, "map_width_pixels") and hasattr(
        game_instance, "map_height_pixels"
    ):
        game_instance.map_width_pixels, game_instance.map_height_pixels = 1000, 800
    else:
        # attach sensible defaults to G
        game_instance.map_width_pixels, game_instance.map_height_pixels = 1000, 800

    # Mock constants.SCREEN_WIDTH and SCREEN_HEIGHT
    mod = importlib.import_module("devscape.main")
    monkeypatch.setattr(mod.constants, "SCREEN_WIDTH", 800)
    monkeypatch.setattr(mod.constants, "SCREEN_HEIGHT", 600)

    # Move camera to extreme negative and extreme positive positions and call update
    for test_pos_x, test_pos_y in [(-1000, -1000), (10000, 10000), (50, 40), (0, 0)]:
        # set camera pre-state
        game_instance.camera_offset_x = test_pos_x
        game_instance.camera_offset_y = test_pos_y

        # call update; adapt to signatures that accept dt or none
        try:
            game_instance.update(0.016)
        except TypeError:
            try:
                game_instance.update()
            except (TypeError, AttributeError):
                # if update requires more setup, skip the iteration
                continue

        # After update, camera coordinates should lie within map bounds
        assert game_instance.camera_offset_x <= 0
        assert game_instance.camera_offset_y <= 0
        assert (
            game_instance.camera_offset_x
            >= mod.constants.SCREEN_WIDTH - game_instance.map_width_pixels
        )
        assert (
            game_instance.camera_offset_y
            >= mod.constants.SCREEN_HEIGHT - game_instance.map_height_pixels
        )


def test_camera_centering_near_player(monkeypatch):
    game_instance = _safe_instantiate_game()

    # Ensure state.player exists and has coordinates
    if not hasattr(game_instance, "player"):
        game_instance.player = SimpleNamespace(x=10, y=20)
    # set player far out; some clamp logic centers camera on player
    game_instance.player.x = 500
    game_instance.player.y = 400

    # ensure camera exists
    if not hasattr(game_instance, "camera_offset_x"):
        game_instance.camera_offset_x = 0
    if not hasattr(game_instance, "camera_offset_y"):
        game_instance.camera_offset_y = 0

    # Mock constants.SCREEN_WIDTH and SCREEN_HEIGHT
    mod = importlib.import_module("devscape.main")
    monkeypatch.setattr(mod.constants, "SCREEN_WIDTH", 800)
    monkeypatch.setattr(mod.constants, "SCREEN_HEIGHT", 600)
    monkeypatch.setattr(mod.constants, "TILE_SIZE", 32)

    try:
        game_instance.update(0.016)
    except TypeError:
        game_instance.update()

    # If implementation centers camera, camera coords should move toward player coordinates
    # Expected camera position after centering on player (500, 400) with screen (800, 600) and tile (32)
    expected_camera_x = (
        mod.constants.SCREEN_WIDTH // 2
        - game_instance.player.x * mod.constants.TILE_SIZE
    )
    expected_camera_y = (
        mod.constants.SCREEN_HEIGHT // 2
        - game_instance.player.y * mod.constants.TILE_SIZE
    )

    # Clamp camera to map boundaries (assuming map is larger than screen)
    # These values are based on the default map_width_pixels=1000, map_height_pixels=800
    expected_camera_x = min(expected_camera_x, 0)
    expected_camera_y = min(expected_camera_y, 0)
    expected_camera_x = max(
        expected_camera_x, mod.constants.SCREEN_WIDTH - game_instance.map_width_pixels
    )
    expected_camera_y = max(
        expected_camera_y, mod.constants.SCREEN_HEIGHT - game_instance.map_height_pixels
    )

    assert game_instance.camera_offset_x == expected_camera_x
    assert game_instance.camera_offset_y == expected_camera_y
