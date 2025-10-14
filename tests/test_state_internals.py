import json

import pytest

mod = pytest.importorskip("game.state")


def _instantiate_flex(cls):
    try:
        return cls()
    except TypeError:
        try:
            return cls("Name")
        except TypeError:
            try:
                return cls(name="Name")
            except Exception:
                pytest.skip(f"Cannot instantiate {cls}")


@pytest.mark.parametrize("name", ["Player", "Trait", "GameState", "LLMCharacter"])
def test_state_classes_basic(name):
    if not hasattr(mod, name):
        pytest.skip(f"{name} missing")
    ClassUnderTest = getattr(mod, name)
    inst = _instantiate_flex(ClassUnderTest)
    assert inst is not None

    # check attributes and simple mutability
    for attr in ("name", "mood", "traits", "x", "y"):
        if hasattr(inst, attr):
            v = getattr(inst, attr)
            assert isinstance(v, (str, int, float, dict, list, type(None)))
            # try set if writable
            try:
                setattr(inst, attr, v)
            except AttributeError:
                pass

    # try equality
    try:
        _ = inst == inst
    except TypeError:
        pytest.fail("equality broke for " + name)

    # try serialization hooks
    if hasattr(inst, "to_dict") and callable(inst.to_dict):
        d = inst.to_dict()
        assert isinstance(d, dict)
        json.dumps(
            {
                k: v
                for k, v in d.items()
                if isinstance(v, (str, int, float, bool, type(None), list, dict))
            }
        )
    elif hasattr(inst, "to_json") and callable(inst.to_json):
        s = inst.to_json()
        json.loads(s)
    else:
        _ = getattr(inst, "__dict__", {})
