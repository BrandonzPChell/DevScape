import pytest

mod = pytest.importorskip("game.state")


def _make_entity(cls):
    try:
        return cls("E", 0, 0, ["X"])
    except TypeError:
        try:
            return cls("E")
        except TypeError:
            return (
                cls(name="E") if "name" in cls.__init__.__code__.co_varnames else cls()
            )


def test_entity_move_diagonal_and_boundaries():
    if not hasattr(mod, "Entity"):
        pytest.skip("Entity not present")
    EntityClass = mod.Entity
    ent = _make_entity(EntityClass)

    # Mock a game_map for boundary and water checks
    game_map = [
        "WWWWWW",
        "W.P.EW",
        "W.W.WW",
        "WWWWWW",
    ]

    # Set initial position
    ent.x, ent.y = 1, 1  # Position at 'P'

    # Test diagonal move (should not move)
    initial_pos = (ent.x, ent.y)
    ent.move(1, 1, game_map)  # Attempt diagonal move
    assert (ent.x, ent.y) == initial_pos

    # Test move into water (should not move)
    ent.move(-1, 0, game_map)  # Attempt move left into 'W'
    assert (ent.x, ent.y) == initial_pos

    # Test valid move (move right)
    ent.move(1, 0, game_map)  # Move right to '.'
    assert (ent.x, ent.y) == (2, 1)

    # Test move out of bounds (should not move)
    ent.x, ent.y = 0, 0  # Set to top-left corner
    ent.move(-1, 0, game_map)  # Attempt move left out of bounds
    assert (ent.x, ent.y) == (0, 0)

    ent.move(0, -1, game_map)  # Attempt move up out of bounds
    assert (ent.x, ent.y) == (0, 0)
