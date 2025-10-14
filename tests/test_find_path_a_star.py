from src.devscape.ollama_ai import _find_path_a_star


def test_find_path_a_star_simple_path():
    game_map = [
        "S.E",
    ]
    start = (0, 0)
    end = (2, 0)
    path = _find_path_a_star(start, end, game_map)
    assert path == [(0, 0), (1, 0), (2, 0)]


def test_find_path_a_star_no_path():
    game_map = [
        "S W E",
    ]
    start = (0, 0)
    end = (4, 0)
    path = _find_path_a_star(start, end, game_map)
    assert path is None


def test_find_path_a_star_with_obstacles():
    game_map = [
        "S..",
        ".W.",
        "..E",
    ]
    start = (0, 0)
    end = (2, 2)
    path = _find_path_a_star(start, end, game_map)
    assert path == [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)]


def test_find_path_a_star_start_is_end():
    game_map = ["S"]
    start = (0, 0)
    end = (0, 0)
    path = _find_path_a_star(start, end, game_map)
    assert path == [(0, 0)]  # A path from a point to itself is just that point
