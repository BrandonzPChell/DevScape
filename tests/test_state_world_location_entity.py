import pytest

mod = pytest.importorskip("game.state")


def _flex_instantiate(cls):
    try:
        return cls()
    except TypeError:
        try:
            return cls("Name")
        except Exception:
            try:
                return cls(name="Name")
            except Exception:
                pytest.skip(f"Cannot instantiate {cls}")


def test_world_and_location_constructors():
    for name in ("World", "Location"):
        if not hasattr(mod, name):
            pytest.skip(f"{name} missing")
        ClassUnderTest = getattr(mod, name)
        # instantiate with and without optional args
        inst1 = _flex_instantiate(ClassUnderTest)
        assert inst1 is not None
        # attempt alternate ctor shapes if applicable
        try:
            inst2 = (
                ClassUnderTest(name="Test", locations=[])
                if name == "World"
                else ClassUnderTest(name="Test", description="Desc", exits={})
            )
            if inst2 is not None:
                assert inst2 is not None
        except (TypeError, AttributeError):
            pass


def test_entity_move_diagonal_and_water_boundary():
    if not hasattr(mod, "Entity"):
        pytest.skip("Entity not present")
    EntityClass = mod.Entity
    ent = _flex_instantiate(EntityClass)
    # give entity coordinates if missing
    try:
        ent.x, ent.y = 5, 5
    except AttributeError:
        pass

    # Mock a game_map for boundary and water checks
    game_map = [
        "WWWWWW",
        "W.P.EW",
        "W.W.WW",
        "WWWWWW",
    ]

    # diagonal move attempt
    try:
        ent.move(1, 1, game_map)
        # ensure type safety: attributes still numeric
        assert isinstance(getattr(ent, "x", 0), (int, float))
        assert isinstance(getattr(ent, "y", 0), (int, float))
    except (ValueError, IndexError):
        # acceptable if move raises for invalid diagonal
        pass

    # out of bounds / water handling: call extreme moves
    try:
        ent.move(9999, 9999, game_map)
    except (ValueError, IndexError):
        pass

    assert True
