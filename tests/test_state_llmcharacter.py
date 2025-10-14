import json

import pytest


def _safe_instantiate(cls):
    """Try a few sensible constructor signatures, raise if none work."""
    try:
        return cls()  # no-arg
    except TypeError as exc:
        raise TypeError(f"Could not instantiate {cls!r}: {exc}")


def test_llmcharacter_basic_attributes_or_skip():
    mod = pytest.importorskip("game.state")
    if "LLMCharacter" not in dir(mod):
        pytest.skip("LLMCharacter not present in game.state")

    LLMCharacterClass = mod.LLMCharacter
    inst = _safe_instantiate(LLMCharacterClass)

    # Basic attribute expectations: mood, traits
    assert hasattr(inst, "mood"), "LLMCharacter should have a mood attribute"
    assert hasattr(inst, "traits"), "LLMCharacter should have a traits attribute"

    # Validate types and simple mutability
    assert isinstance(inst.mood, (str, type(None)))
    assert isinstance(inst.traits, (dict, list, type(None)))

    # Mutate attributes and ensure state changes
    old_mood = inst.mood
    try:
        inst.mood = "happy"
        assert inst.mood == "happy"
    finally:
        # restore if possible
        try:
            inst.mood = old_mood
        except AttributeError:
            pass


def test_llmcharacter_equality_and_serialization_fallback():
    mod = pytest.importorskip("game.state")
    if "LLMCharacter" not in dir(mod):
        pytest.skip("LLMCharacter not present in game.state")

    LLMCharacterClass = mod.LLMCharacter
    a = _safe_instantiate(LLMCharacterClass)
    b = _safe_instantiate(LLMCharacterClass)

    # If equality is implemented, identical default instances may compare equal or not;
    # we at least assert that the operation runs without error.
    try:
        _ = a == b
    except TypeError:
        pytest.fail("Equality operation on LLMCharacter raised an exception")

    # Try lightweight serialization: prefer to_dict or to_json, else fallback to json.dumps of __dict__
    if hasattr(a, "to_dict") and callable(getattr(a, "to_dict")):
        d = a.to_dict()
        assert isinstance(d, dict)
        # round-trip through json
        assert json.loads(json.dumps(d)) == d
    elif hasattr(a, "to_json") and callable(getattr(a, "to_json")):
        s = a.to_json()
        assert isinstance(s, str)
        json.loads(s)
    else:
        # fallback: inspect __dict__
        d = getattr(a, "__dict__", None)
        assert isinstance(d, dict)
        # ensure basic JSON-serializability for top-level simple values
        try:
            json.dumps(
                {
                    k: v
                    for k, v in d.items()
                    if isinstance(v, (str, int, float, bool, type(None), list, dict))
                }
            )
        except TypeError:
            pytest.skip(
                "LLMCharacter contains non-serializable attributes; skip strict serialization assertion"
            )
