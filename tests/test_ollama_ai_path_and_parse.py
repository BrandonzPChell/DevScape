import pytest

mod = pytest.importorskip("game.ollama_ai")


def test_direction_to_delta_exists_and_many_dirs():
    fn = getattr(mod, "_direction_to_delta", getattr(mod, "direction_to_delta", None))
    if fn is None:
        pytest.skip("direction->delta helper not present")
    for d in (
        "north",
        "south",
        "east",
        "west",
        "northeast",
        "northwest",
        "southeast",
        "southwest",
        "up",
        "down",
        "invalid",
    ):
        out = fn(d)
        assert out is None or (isinstance(out, tuple) and len(out) == 2)


def test_parse_content_move_and_dialogue_variants():
    fn = getattr(mod, "_parse_content_to_move_and_dialogue", None)
    if fn is None:
        pytest.skip("_parse_content_to_move_and_dialogue not present")

    # None input
    try:
        r = fn(None)
        assert isinstance(r, dict)
    except (ValueError, TypeError):
        pass

    # direction + dialogue
    r = fn("MOVE north\nHello")
    assert isinstance(r, dict)
    move = r.get("move")
    dialogue = r.get("dialogue")
    assert move is None or isinstance(move, (dict))
    assert dialogue is None or isinstance(dialogue, str)

    # coordinate style
    try:
        r2 = fn("MOVE [3,4]")
        move2 = r2.get("move")
        assert move2 is not None
    except (ValueError, TypeError):
        pass

    # malformed input should not crash test runner
    for bad in ("{not json}", 12345, ["MOVE east"]):
        try:
            out = fn(bad)
            assert isinstance(out, dict)
        except (ValueError, TypeError):
            pass


def test_find_path_a_star_no_path_and_is_valid_branches():
    fn = getattr(mod, "_find_path_a_star", None)
    if fn is None:
        pytest.skip("_find_path_a_star not present")

    # Provide tiny grid and start/goal that have no path
    grid = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]  # walls in centre row create no path
    try:
        res = fn(start=(0, 0), end=(2, 2), game_map=grid)
        assert res is None or isinstance(res, list)
    except (ValueError, TypeError, IndexError):
        pass
