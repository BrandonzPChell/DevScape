import json
from pathlib import Path

import jsonschema
import pytest

from src.devscape import db_scroll, engine, state_scroll

# Define paths for test files
TEST_STATE_FILE = Path(__file__).parent.parent.parent / "test_state.json"
TEST_DB_FILE = Path(__file__).parent.parent.parent / "test_lineage.db"


@pytest.fixture(autouse=True)
def setup_and_teardown_test_environment():
    # Temporarily redirect state and db files for testing
    original_state_file = state_scroll.STATE_FILE
    original_db_file = db_scroll.DB_FILE

    state_scroll.STATE_FILE = TEST_STATE_FILE
    db_scroll.DB_FILE = TEST_DB_FILE

    # Ensure test files are clean before each test
    if TEST_STATE_FILE.exists():
        TEST_STATE_FILE.unlink()
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    # Initialize a clean database for each test
    db_scroll.initialize_db()

    # Provide a minimal valid state for tests that need it
    initial_valid_state = {
        "player": {"name": "Test Steward", "level": 1, "health": 100, "inventory": []},
        "traits": [],
        "quests": [],
        "planetary_feedback": {
            "mood": "calm",
            "last_event": "2025-10-12T00:00:00Z",
            "events_log": [],
        },
    }
    state_scroll.save_state(initial_valid_state)

    yield  # Run the test

    # Clean up after each test
    if TEST_STATE_FILE.exists():
        TEST_STATE_FILE.unlink()
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    # Restore original file paths
    state_scroll.STATE_FILE = original_state_file
    db_scroll.DB_FILE = original_db_file


def test_state_validation_rejects_invalid_data():
    # Attempt to save an invalid state (missing required 'player' field)
    invalid_state = {
        "traits": [],
        "quests": [],
        "planetary_feedback": {
            "mood": "calm",
            "last_event": "2025-10-12T00:00:00Z",
            "events_log": [],
        },
    }
    with pytest.raises(jsonschema.exceptions.ValidationError):
        state_scroll.save_state(invalid_state)


def test_event_bus_updates_state_for_trait_evolved():
    # Trigger a trait_evolved event
    event_payload = {
        "trait_id": "strength",
        "new_level": 3,
        "contributor_id": "TestUser",
        "description": "Strength increased.",
    }
    engine.event_bus.publish("trait_evolved", event_payload)

    # Load state and verify the trait was added/updated
    updated_state = state_scroll.load_state()
    assert any(
        t["trait_id"] == "strength" and t["level"] == 3 for t in updated_state["traits"]
    )


def test_event_bus_records_lineage_for_trait_evolved():
    # Trigger a trait_evolved event
    event_payload = {
        "trait_id": "agility",
        "new_level": 2,
        "contributor_id": "TestUser",
        "description": "Agility improved.",
    }
    engine.event_bus.publish("trait_evolved", event_payload)

    # Fetch lineage and verify the event was recorded
    lineage_entries = db_scroll.fetch_lineage()
    assert len(lineage_entries) == 1
    assert json.loads(lineage_entries[0]["details"]) == {
        "event_type": "trait_evolved",
        "payload": event_payload,
    }


def test_event_bus_updates_state_for_item_acquired():
    # Trigger an item_acquired event
    event_payload = {
        "item_id": "healing_potion",
        "quantity": 5,
        "contributor_id": "TestUser",
    }
    engine.event_bus.publish("item_acquired", event_payload)

    # Load state and verify the item was added to inventory
    updated_state = state_scroll.load_state()
    assert any(
        item["item_id"] == "healing_potion" and item["quantity"] == 5
        for item in updated_state["player"]["inventory"]
    )


def test_event_bus_records_lineage_for_item_acquired():
    # Trigger an item_acquired event
    event_payload = {
        "item_id": "mana_crystal",
        "quantity": 1,
        "contributor_id": "TestUser",
    }
    engine.event_bus.publish("item_acquired", event_payload)

    # Fetch lineage and verify the event was recorded
    lineage_entries = db_scroll.fetch_lineage()
    assert len(lineage_entries) == 1
    assert lineage_entries[0]["action_type"] == "item_acquired"
    assert lineage_entries[0]["contributor_id"] == "TestUser"
    assert json.loads(lineage_entries[0]["details"]) == {
        "event_type": "item_acquired",
        "payload": event_payload,
    }
