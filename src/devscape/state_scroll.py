import json
from pathlib import Path

import jsonschema

STATE_FILE = Path(__file__).parent.parent.parent / "state.json"
SCHEMA_FILE = Path(__file__).parent.parent.parent / "state.schema.json"


def load_schema():
    """
    Loads the JSON schema for state validation.
    """
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state():
    """
    Loads the game state from state.json and validates it against the schema.
    """
    if not STATE_FILE.exists():
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)
    schema = load_schema()
    jsonschema.validate(instance=state, schema=schema)
    return state


def save_state(state):
    """
    Saves the game state to state.json after validating it against the schema.
    """
    schema = load_schema()
    jsonschema.validate(instance=state, schema=schema)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
