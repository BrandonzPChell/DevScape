import json

import pytest

mod = pytest.importorskip("game.state")


def _try_inst(cls):
    try:
        return cls()
    except TypeError:
        try:
            return cls("Name")
        except TypeError:
            # try kwargs
            try:
                return cls(name="Name")
            except Exception:
                pytest.skip(f"Unable to instantiate {cls}")


@pytest.mark.parametrize("clsname", ["GameState", "Player", "Trait", "LLMCharacter"])
def test_state_class_smoke_and_mutation(clsname):
    if not hasattr(mod, clsname):
        pytest.skip(f"{clsname} not present")
    ClassUnderTest = getattr(mod, clsname)
    inst = _try_inst(ClassUnderTest)
    assert inst is not None

    # Common property checks when present
    for attr in ("name", "mood", "traits", "x", "y"):
        if hasattr(inst, attr):
            val = getattr(inst, attr)
            # check reading does not raise and basic types are sane
            assert isinstance(val, (str, int, float, dict, list, type(None)))

    # Try setting a simple attribute if writable
    if hasattr(inst, "name"):
        old = getattr(inst, "name")
        try:
            setattr(inst, "name", "X")
            assert getattr(inst, "name") == "X"
        finally:
            # restore if possible
            try:
                setattr(inst, "name", old)
            except AttributeError:
                pass


def test_state_serialization_if_present():
    for clsname in ("GameState", "LLMCharacter"):
        if not hasattr(mod, clsname):
            continue
        cls = getattr(mod, clsname)
        inst = _try_inst(cls)
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
        else:
            _ = getattr(inst, "__dict__", {})
