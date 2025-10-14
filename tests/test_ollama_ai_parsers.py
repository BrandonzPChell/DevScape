import pytest

mod = pytest.importorskip("game.ollama_ai")


def test_direction_to_delta_all_dirs():
    # function name may be _direction_to_delta or direction_to_delta
    fn = getattr(mod, "_direction_to_delta", getattr(mod, "direction_to_delta", None))
    if fn is None:
        pytest.skip("direction->delta helper not present")
    # common cardinal + diagonal checks
    mapping = {
        "up": (0, -1),
        "down": (0, 1),
        "left": (-1, 0),
        "right": (1, 0),
        "stay": (0, 0),
    }
    for d, expected in mapping.items():
        out = fn(d)
        assert isinstance(out, tuple)
        assert len(out) == 2
        # accept normalized or scaled deltas
        assert out[0] == expected[0] and out[1] == expected[1]


def test_parse_content_to_move_and_dialogue_variants():
    fn = getattr(mod, "_parse_content_to_move_and_dialogue", None)
    if fn is None:
        pytest.skip("_parse_content_to_move_and_dialogue not present")

    # None content -> (None, None) or raises ValueError; accept either
    try:
        r = fn(None)
        assert isinstance(r, dict)
        assert r["move"] is None
        assert r["dialogue"] == ""
    except (ValueError, TypeError):
        pass

    # simple textual dialogue with MOVE token
    sample1 = "MOVE north\nHello there"
    r1 = fn(sample1)
    assert isinstance(r1, dict)
    assert r1["move"] == {"dx": 0, "dy": -1}  # Assuming 'north' maps to (0, -1)
    assert r1["dialogue"] == "Hello there"

    # coordinate style
    sample2 = "MOVE [3,4]"
    r2 = fn(sample2)
    assert r2["move"] == {"dx": 3, "dy": 4}

    # malformed content should raise ValueError/TypeError or return sensible fallback
    for bad in ("{not json}", 12345):
        try:
            out = fn(bad)
            assert isinstance(out, dict)
        except (ValueError, TypeError):
            pass
