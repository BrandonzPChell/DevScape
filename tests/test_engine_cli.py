import json
from unittest.mock import ANY, patch

import pytest
from click.testing import CliRunner

from src.devscape import db_scroll, engine, state_scroll


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_state():
    return {
        "player": {"name": "Test Steward", "level": 1, "health": 100, "inventory": []},
        "traits": [],
        "quests": [],
        "planetary_feedback": {
            "mood": "calm",
            "last_event": "2025-10-12T00:00:00Z",
            "events_log": [],
        },
    }


@pytest.fixture
def mock_onboarding_config():
    return {"title": "DevScape Onboarding"}


@pytest.fixture
def mock_prompts_config():
    return ["prompt1", "prompt2"]


def test_status_command_output(
    runner, mock_state, mock_onboarding_config, mock_prompts_config
):
    with patch.object(state_scroll, "load_state", return_value=mock_state):
        with patch.object(db_scroll, "fetch_lineage", return_value=[]):
            with patch.object(
                engine.config_scroll,
                "get_onboarding_config",
                return_value=mock_onboarding_config,
            ):
                with patch.object(
                    engine.config_scroll,
                    "get_prompts_config",
                    return_value=mock_prompts_config,
                ):
                    result = runner.invoke(engine.cli, ["status", "--name", "TestUser"])

                    assert result.exit_code == 0
                    assert (
                        "Welcome, TestUser, to the DevScape Ritual Status!"
                        in result.output
                    )
                    assert "--- Config Scrolls 📜 ---" in result.output
                    assert "Title: DevScape Onboarding" in result.output
                    assert "Prompts: 2 loaded" in result.output
                    assert "--- Heart's Pulse (Current State) ❤️ ---" in result.output
                    assert "Player: Test Steward (Level 1) Health: 100" in result.output
                    assert "Traits ✨:" in result.output
                    assert "No traits evolved yet." in result.output
                    assert "Quests 🗺️:" in result.output
                    assert "No active quests." in result.output
                    assert "Planetary Mood 😊: calm" in result.output
                    assert "Last Planetary Event: 2025-10-12T00:00:00Z" in result.output
                    assert (
                        "--- Lineage Archive (Recent Entries) 📜 ---" in result.output
                    )
                    assert "No lineage entries found." in result.output
                    assert (
                        "May your journey be guided by wisdom and your glyphs be true."
                        in result.output
                    )


def test_evolve_command(runner):
    with patch.object(engine.event_bus, "publish") as mock_publish:
        result = runner.invoke(
            engine.cli, ["evolve", "wisdom", "5", "--contributor", "TestUser"]
        )

        assert result.exit_code == 0
        assert "Attempting to evolve trait 'wisdom' to level 5..." in result.output
        assert (
            "Trait 'wisdom' evolved to level 5 and lineage inscribed." in result.output
        )
        mock_publish.assert_called_once_with(
            "trait_evolved",
            {
                "trait_id": "wisdom",
                "new_level": 5,
                "contributor_id": "TestUser",
                "description": "Trait wisdom evolved to level 5.",
            },
        )


def test_feedback_command(runner):
    with patch.object(engine.event_bus, "publish") as mock_publish:
        result = runner.invoke(
            engine.cli, ["feedback", "joy", "--contributor", "TestUser"]
        )

        assert result.exit_code == 0
        assert "Logging planetary mood: 'joy'..." in result.output
        assert "Planetary mood 'joy' logged and lineage inscribed." in result.output
        mock_publish.assert_called_once_with(
            "planetary_feedback",
            {
                "mood": "joy",
                "contributor_id": "TestUser",
                "timestamp": ANY,
                "description": "Planetary mood set to joy.",
            },
        )


def test_quest_start_command(runner):
    with patch.object(engine.event_bus, "publish") as mock_publish:
        result = runner.invoke(
            engine.cli, ["quest", "start", "test_quest_id", "--contributor", "TestUser"]
        )

        assert result.exit_code == 0
        assert "Attempting to start quest 'test_quest_id'..." in result.output
        assert "Quest 'test_quest_id' started and lineage inscribed." in result.output
        mock_publish.assert_called_once_with(
            "quest_started",
            {
                "quest_id": "test_quest_id",
                "status": "active",
                "progress": 0,
                "contributor_id": "TestUser",
                "description": "Quest test_quest_id started.",
            },
        )


def test_quest_complete_command(runner):
    with patch.object(engine.event_bus, "publish") as mock_publish:
        result = runner.invoke(
            engine.cli,
            ["quest", "complete", "test_quest_id", "--contributor", "TestUser"],
        )

        assert result.exit_code == 0
        assert "Attempting to complete quest 'test_quest_id'..." in result.output
        assert "Quest 'test_quest_id' completed and lineage inscribed." in result.output
        mock_publish.assert_called_once_with(
            "quest_completed",
            {
                "quest_id": "test_quest_id",
                "status": "completed",
                "progress": 100,
                "contributor_id": "TestUser",
                "description": "Quest test_quest_id completed.",
            },
        )


def test_trigger_event_command(runner):
    with patch.object(engine.event_bus, "publish") as mock_publish:
        payload = {
            "trait_id": "intelligence",
            "new_level": 10,
            "contributor_id": "TestUser",
        }
        result = runner.invoke(
            engine.cli, ["trigger-event", "trait_evolved", json.dumps(payload)]
        )

        assert result.exit_code == 0
        assert (
            f"Event 'trait_evolved' triggered successfully with payload: {payload}"
            in result.output
        )
        mock_publish.assert_called_once_with("trait_evolved", payload)


def test_trigger_event_command_invalid_json(runner):
    with patch.object(engine.event_bus, "publish") as mock_publish:
        result = runner.invoke(
            engine.cli, ["trigger-event", "trait_evolved", "invalid_json"]
        )

        assert result.exit_code == 0
        assert "Error: Payload must be a valid JSON string." in result.output
        mock_publish.assert_not_called()
