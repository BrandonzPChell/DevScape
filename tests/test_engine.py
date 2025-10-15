import json
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from devscape import config_scroll, db_scroll, engine, state_scroll


@pytest.fixture
def runner():
    return CliRunner()


def test_status_command_success(runner, mocker):
    mock_onboarding_config = {"title": "Test Onboarding"}
    mock_prompts_config = ["prompt1", "prompt2"]
    mock_current_state = {
        "player": {"name": "Hero", "level": 1, "health": 100},
        "traits": [{"trait_id": "strength", "level": 5, "description": "Strong"}],
        "quests": [{"quest_id": "quest1", "status": "active", "progress": 50}],
        "planetary_feedback": {"mood": "calm", "last_event": "2023-01-01T12:00:00"},
    }
    mock_recent_lineage = [
        {
            "action_type": "trait_evolved",
            "contributor_id": "User1",
            "timestamp": "2023-01-01T10:00:00",
            "details": json.dumps(
                {
                    "event_type": "trait_evolved",
                    "payload": {
                        "trait_id": "strength",
                        "new_level": 5,
                        "contributor_id": "User1",
                        "timestamp": "2023-01-01T10:00:00",
                    },
                }
            ),
        }
    ]

    mocker.patch.object(
        config_scroll, "get_onboarding_config", return_value=mock_onboarding_config
    )
    mocker.patch.object(
        config_scroll, "get_prompts_config", return_value=mock_prompts_config
    )
    mocker.patch.object(state_scroll, "load_state", return_value=mock_current_state)
    mocker.patch.object(db_scroll, "fetch_lineage", return_value=mock_recent_lineage)

    result = runner.invoke(engine.cli, ["status"])

    assert result.exit_code == 0
    assert "Welcome, Steward, to the DevScape Ritual Status!" in result.output
    assert "Title: Test Onboarding" in result.output
    assert "Prompts: 2 loaded" in result.output
    assert "Player: Hero (Level 1) Health: 100" in result.output
    assert "strength: █████░░░░░ Level 5 - Strong" in result.output
    assert "[⏳] quest1: active (50%) " in result.output
    assert "Planetary Mood 😊: calm" in result.output
    assert "Last Planetary Event: 2023-01-01T12:00:00" in result.output
    assert (
        "✨ [2023-01-01T10:00:00] User1 evolved strength to level 5." in result.output
    )
    assert (
        "May your journey be guided by wisdom and your glyphs be true." in result.output
    )


def test_status_command_state_file_not_found(runner, mocker):
    mocker.patch.object(config_scroll, "get_onboarding_config", return_value={})
    mocker.patch.object(config_scroll, "get_prompts_config", return_value=[])
    mocker.patch.object(state_scroll, "load_state", side_effect=FileNotFoundError)
    mocker.patch.object(db_scroll, "fetch_lineage", return_value=[])

    result = runner.invoke(engine.cli, ["status"])

    assert result.exit_code == 0
    assert (
        "Error: State file not found. Has the game state been initialized?"
        in result.output
    )


def test_status_command_state_load_exception(runner, mocker):
    mocker.patch.object(config_scroll, "get_onboarding_config", return_value={})
    mocker.patch.object(config_scroll, "get_prompts_config", return_value=[])
    mocker.patch.object(state_scroll, "load_state", side_effect=Exception("Test Error"))
    mocker.patch.object(db_scroll, "fetch_lineage", return_value=[])

    result = runner.invoke(engine.cli, ["status"])

    assert result.exit_code == 0
    assert (
        "An unexpected error occurred while loading state: Test Error" in result.output
    )


def test_status_command_no_traits(runner, mocker):
    mock_current_state = {
        "player": {"name": "Hero", "level": 1, "health": 100},
        "traits": [],
        "quests": [],
        "planetary_feedback": {"mood": "calm", "last_event": "2023-01-01T12:00:00"},
    }
    mocker.patch.object(config_scroll, "get_onboarding_config", return_value={})
    mocker.patch.object(config_scroll, "get_prompts_config", return_value=[])
    mocker.patch.object(state_scroll, "load_state", return_value=mock_current_state)
    mocker.patch.object(db_scroll, "fetch_lineage", return_value=[])

    result = runner.invoke(engine.cli, ["status"])
    assert result.exit_code == 0
    assert "No traits evolved yet." in result.output


def test_status_command_no_quests(runner, mocker):
    mock_current_state = {
        "player": {"name": "Hero", "level": 1, "health": 100},
        "traits": [],
        "quests": [],
        "planetary_feedback": {"mood": "calm", "last_event": "2023-01-01T12:00:00"},
    }
    mocker.patch.object(config_scroll, "get_onboarding_config", return_value={})
    mocker.patch.object(config_scroll, "get_prompts_config", return_value=[])
    mocker.patch.object(state_scroll, "load_state", return_value=mock_current_state)
    mocker.patch.object(db_scroll, "fetch_lineage", return_value=[])

    result = runner.invoke(engine.cli, ["status"])
    assert result.exit_code == 0
    assert "No active quests." in result.output


def test_status_command_no_lineage(runner, mocker):
    mock_current_state = {
        "player": {"name": "Hero", "level": 1, "health": 100},
        "traits": [],
        "quests": [],
        "planetary_feedback": {"mood": "calm", "last_event": "2023-01-01T12:00:00"},
    }
    mocker.patch.object(config_scroll, "get_onboarding_config", return_value={})
    mocker.patch.object(config_scroll, "get_prompts_config", return_value=[])
    mocker.patch.object(state_scroll, "load_state", return_value=mock_current_state)
    mocker.patch.object(db_scroll, "fetch_lineage", return_value=[])

    result = runner.invoke(engine.cli, ["status"])
    assert result.exit_code == 0
    assert "No lineage entries found." in result.output


def test_status_command_mood_unrest(runner, mocker):
    mock_current_state = {
        "player": {"name": "Hero", "level": 1, "health": 100},
        "traits": [],
        "quests": [],
        "planetary_feedback": {"mood": "unrest", "last_event": "2023-01-01T12:00:00"},
    }
    mocker.patch.object(config_scroll, "get_onboarding_config", return_value={})
    mocker.patch.object(config_scroll, "get_prompts_config", return_value=[])
    mocker.patch.object(state_scroll, "load_state", return_value=mock_current_state)
    mocker.patch.object(db_scroll, "fetch_lineage", return_value=[])

    result = runner.invoke(engine.cli, ["status"])
    assert result.exit_code == 0
    assert "Planetary Mood 😟: unrest" in result.output


def test_status_command_mood_joy(runner, mocker):
    mock_current_state = {
        "player": {"name": "Hero", "level": 1, "health": 100},
        "traits": [],
        "quests": [],
        "planetary_feedback": {"mood": "joy", "last_event": "2023-01-01T12:00:00"},
    }
    mocker.patch.object(config_scroll, "get_onboarding_config", return_value={})
    mocker.patch.object(config_scroll, "get_prompts_config", return_value=[])
    mocker.patch.object(state_scroll, "load_state", return_value=mock_current_state)
    mocker.patch.object(db_scroll, "fetch_lineage", return_value=[])

    result = runner.invoke(engine.cli, ["status"])
    assert result.exit_code == 0
    assert "Planetary Mood 🌟: joy" in result.output


def test_status_command_mood_unknown(runner, mocker):
    mock_current_state = {
        "player": {"name": "Hero", "level": 1, "health": 100},
        "traits": [],
        "quests": [],
        "planetary_feedback": {"mood": "unknown", "last_event": "2023-01-01T12:00:00"},
    }
    mocker.patch.object(config_scroll, "get_onboarding_config", return_value={})
    mocker.patch.object(config_scroll, "get_prompts_config", return_value=[])
    mocker.patch.object(state_scroll, "load_state", return_value=mock_current_state)
    mocker.patch.object(db_scroll, "fetch_lineage", return_value=[])

    result = runner.invoke(engine.cli, ["status"])
    assert result.exit_code == 0
    assert "Planetary Mood ❓: unknown" in result.output


def test_evolve_command(runner, mocker):
    mock_publish = mocker.patch.object(engine.event_bus, "publish")
    result = runner.invoke(
        engine.cli, ["evolve", "wisdom", "10", "--contributor", "TestUser"]
    )

    assert result.exit_code == 0
    assert "Attempting to evolve trait 'wisdom' to level 10..." in result.output
    mock_publish.assert_called_once_with(
        "trait_evolved",
        {
            "trait_id": "wisdom",
            "new_level": 10,
            "contributor_id": "TestUser",
            "description": "Trait wisdom evolved to level 10.",
        },
    )
    assert "Trait 'wisdom' evolved to level 10 and lineage inscribed." in result.output


def test_feedback_command(runner, mocker):
    mock_publish = mocker.patch.object(engine.event_bus, "publish")
    mock_datetime = mocker.patch("devscape.engine.datetime")
    mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)

    result = runner.invoke(
        engine.cli, ["feedback", "calm", "--contributor", "TestUser"]
    )

    assert result.exit_code == 0
    assert "Logging planetary mood: 'calm'..." in result.output
    mock_publish.assert_called_once_with(
        "planetary_feedback",
        {
            "mood": "calm",
            "contributor_id": "TestUser",
            "timestamp": "2023-01-01T12:00:00",
            "description": "Planetary mood set to calm.",
        },
    )
    assert "Planetary mood 'calm' logged and lineage inscribed." in result.output


def test_quest_start_command(runner, mocker):
    mock_publish = mocker.patch.object(engine.event_bus, "publish")
    result = runner.invoke(
        engine.cli, ["quest", "start", "first_journey", "--contributor", "QuestGiver"]
    )

    assert result.exit_code == 0
    assert "Attempting to start quest 'first_journey'..." in result.output
    mock_publish.assert_called_once_with(
        "quest_started",
        {
            "quest_id": "first_journey",
            "status": "active",
            "progress": 0,
            "contributor_id": "QuestGiver",
            "description": "Quest first_journey started.",
        },
    )
    assert "Quest 'first_journey' started and lineage inscribed." in result.output


def test_quest_complete_command(runner, mocker):
    mock_publish = mocker.patch.object(engine.event_bus, "publish")
    result = runner.invoke(
        engine.cli,
        ["quest", "complete", "first_journey", "--contributor", "QuestCompleter"],
    )

    assert result.exit_code == 0
    assert "Attempting to complete quest 'first_journey'..." in result.output
    mock_publish.assert_called_once_with(
        "quest_completed",
        {
            "quest_id": "first_journey",
            "status": "completed",
            "progress": 100,
            "contributor_id": "QuestCompleter",
            "description": "Quest first_journey completed.",
        },
    )
    assert "Quest 'first_journey' completed and lineage inscribed." in result.output


def test_trigger_event_command_success(runner, mocker):
    mock_publish = mocker.patch.object(engine.event_bus, "publish")
    event_type = "test_event"
    payload = '{"key": "value"}'
    result = runner.invoke(engine.cli, ["trigger-event", event_type, payload])

    assert result.exit_code == 0
    assert (
        f"Event '{event_type}' triggered successfully with payload: {{'key': 'value'}}"
        in result.output
    )
    mock_publish.assert_called_once_with(event_type, {"key": "value"})


def test_trigger_event_command_invalid_json(runner, mocker):
    mock_publish = mocker.patch.object(engine.event_bus, "publish")
    event_type = "test_event"
    payload = "invalid_json"
    result = runner.invoke(engine.cli, ["trigger-event", event_type, payload])

    assert result.exit_code == 0
    assert "Error: Payload must be a valid JSON string." in result.output
    mock_publish.assert_not_called()


def test_trigger_event_command_exception(runner, mocker):
    mock_publish = mocker.patch.object(
        engine.event_bus, "publish", side_effect=Exception("Publish Error")
    )
    event_type = "test_event"
    payload = '{"key": "value"}'
    result = runner.invoke(engine.cli, ["trigger-event", event_type, payload])

    assert result.exit_code == 0
    assert "An unexpected error occurred: Publish Error" in result.output
    mock_publish.assert_called_once_with(event_type, {"key": "value"})


def test_event_bus_subscribe_and_publish():
    mock_listener1 = MagicMock()
    mock_listener2 = MagicMock()

    event_bus = engine.EventBus()
    event_bus.subscribe("test_event", mock_listener1)
    event_bus.subscribe("test_event", mock_listener2)
    event_bus.publish("test_event", {"data": "test"})

    mock_listener1.assert_called_once_with("test_event", {"data": "test"})
    mock_listener2.assert_called_once_with("test_event", {"data": "test"})


def test_event_bus_publish_no_listeners():
    mock_listener = MagicMock()
    event_bus = engine.EventBus()
    event_bus.publish("another_event", {"data": "test"})

    mock_listener.assert_not_called()


def test_handle_state_update_handler_found(mocker):
    mock_load_state = mocker.patch.object(state_scroll, "load_state", return_value={})
    mock_save_state = mocker.patch.object(state_scroll, "save_state")
    mocker.patch.dict(engine._STATE_UPDATE_HANDLERS, {"test_event": MagicMock()})  # pylint: disable=protected-access

    engine.handle_state_update("test_event", {"key": "value"})

    mock_load_state.assert_called_once()
    engine._STATE_UPDATE_HANDLERS["test_event"].assert_called_once_with(
        {}, {"key": "value"}
    )
    mock_save_state.assert_called_once_with({})


def test_handle_state_update_no_handler_found(mocker):
    mock_load_state = mocker.patch.object(state_scroll, "load_state", return_value={})
    mock_save_state = mocker.patch.object(state_scroll, "save_state")
    mocker.patch.dict(
        engine._STATE_UPDATE_HANDLERS, clear=True
    )  # Clear all handlers # pylint: disable=protected-access

    with patch("click.echo") as mock_echo:
        engine.handle_state_update("non_existent_event", {"key": "value"})
        mock_echo.assert_any_call(
            "Warning: No state update handler for event type: non_existent_event"
        )
        mock_echo.assert_any_call("State updated for event: non_existent_event")
        assert mock_echo.call_count == 2
    mock_load_state.assert_called_once()
    mock_save_state.assert_called_once_with({})


def test_handle_lineage_recording(mocker):
    mock_record_lineage_event = mocker.patch.object(db_scroll, "record_lineage_event")
    event_type = "test_event"
    payload = {"contributor_id": "TestUser", "data": "some data"}

    engine.handle_lineage_recording(event_type, payload)

    mock_record_lineage_event.assert_called_once_with(
        payload.get("contributor_id", "system"),
        event_type,
        json.dumps({"event_type": event_type, "payload": payload}),
    )


def test_update_state_planetary_feedback(mocker):
    current_state = {
        "planetary_feedback": {
            "mood": "old",
            "last_event": "old_time",
            "events_log": [],
        }
    }
    payload = {"mood": "new", "timestamp": "new_time", "description": "New mood"}
    mocker.patch(
        "devscape.engine.uuid.uuid4",
        return_value=uuid.UUID("12345678-1234-5678-1234-567812345678"),
    )
    mock_datetime = mocker.patch("devscape.engine.datetime")
    mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)

    engine._update_state_planetary_feedback(current_state, payload)  # pylint: disable=protected-access

    assert current_state["planetary_feedback"]["mood"] == "new"
    assert current_state["planetary_feedback"]["last_event"] == "new_time"
    assert len(current_state["planetary_feedback"]["events_log"]) == 1
    assert (
        current_state["planetary_feedback"]["events_log"][0]["event_id"]
        == "12345678-1234-5678-1234-567812345678"
    )
    assert (
        current_state["planetary_feedback"]["events_log"][0]["timestamp"] == "new_time"
    )
    assert (
        current_state["planetary_feedback"]["events_log"][0]["description"]
        == "New mood"
    )


def test_update_state_quest_completed(mocker):
    current_state = {
        "quests": [
            {"quest_id": "q1", "status": "active"},
            {"quest_id": "q2", "status": "active"},
        ]
    }
    payload = {"quest_id": "q1", "status": "completed"}

    engine._update_state_quest_completed(current_state, payload)  # pylint: disable=protected-access

    assert current_state["quests"][0]["status"] == "completed"
    assert current_state["quests"][1]["status"] == "active"


def test_update_state_quest_started(mocker):
    current_state = {"quests": []}
    payload = {"quest_id": "q1", "status": "active", "progress": 0}

    engine._update_state_quest_started(current_state, payload)  # pylint: disable=protected-access

    assert len(current_state["quests"]) == 1
    assert current_state["quests"][0] == {
        "quest_id": "q1",
        "status": "active",
        "progress": 0,
    }


def test_update_state_quest_started_already_exists(mocker):
    current_state = {"quests": [{"quest_id": "q1", "status": "active"}]}
    payload = {"quest_id": "q1", "status": "active", "progress": 0}

    engine._update_state_quest_started(current_state, payload)  # pylint: disable=protected-access
    assert len(current_state["quests"]) == 1  # Should not add duplicate


def test_update_state_item_acquired_new_item(mocker):
    current_state = {"player": {"inventory": []}}
    payload = {"item_id": "sword", "quantity": 1}
    engine._update_state_item_acquired(current_state, payload)  # pylint: disable=protected-access

    assert len(current_state["player"]["inventory"]) == 1
    assert current_state["player"]["inventory"][0] == {
        "item_id": "sword",
        "quantity": 1,
    }


def test_update_state_item_acquired_existing_item(mocker):
    current_state = {"player": {"inventory": [{"item_id": "sword", "quantity": 1}]}}
    payload = {"item_id": "sword", "quantity": 2}

    engine._update_state_item_acquired(current_state, payload)  # pylint: disable=protected-access

    assert len(current_state["player"]["inventory"]) == 1
    assert current_state["player"]["inventory"][0] == {
        "item_id": "sword",
        "quantity": 3,
    }


def test_update_state_trait_evolved_new_trait(mocker):
    current_state = {"traits": []}
    payload = {"trait_id": "agility", "new_level": 3, "description": "Agility evolved"}

    engine._update_state_trait_evolved(current_state, payload)  # pylint: disable=protected-access

    assert len(current_state["traits"]) == 1
    assert current_state["traits"][0] == {
        "trait_id": "agility",
        "level": 3,
        "description": "Agility evolved",
    }


def test_update_state_trait_evolved_existing_trait(mocker):
    current_state = {
        "traits": [{"trait_id": "agility", "level": 2, "description": "Old agility"}]
    }
    payload = {"trait_id": "agility", "new_level": 3, "description": "Agility evolved"}

    engine._update_state_trait_evolved(current_state, payload)  # pylint: disable=protected-access

    assert len(current_state["traits"]) == 1
    assert current_state["traits"][0] == {
        "trait_id": "agility",
        "level": 3,
        "description": "Agility evolved",
    }


def test_cli_initializes_db(runner, mocker):
    mock_initialize_db = mocker.patch.object(db_scroll, "initialize_db")
    engine.cli.callback()
    mock_initialize_db.assert_called_once()
