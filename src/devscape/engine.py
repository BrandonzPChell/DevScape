import json
import sys
import uuid
from datetime import datetime

import click

# Configure stdout for UTF-8 to handle special characters on Windows
from . import config_scroll, db_scroll, state_scroll

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore


def _display_traits(traits):
    if traits:
        for trait in traits:
            bar_length = 10
            filled_blocks = int((trait["level"] / 10) * bar_length)
            empty_blocks = bar_length - filled_blocks
            trait_bar = "█" * filled_blocks + "░" * empty_blocks
            click.echo(
                f"    - {trait['trait_id']}: {trait_bar} Level {trait['level']} - {trait['description']}"
            )
    else:
        click.echo("    No traits evolved yet.")


def _display_quests(quests):
    if quests:
        for q in quests:
            status_glyph = (
                "✅"
                if q["status"] == "completed"
                else "⏳" if q["status"] == "active" else "❌"
            )
            quest_banner = (
                f"[{status_glyph}] {q['quest_id']}: {q['status']} ({q['progress']}%) "
            )
            if q["status"] == "completed":
                quest_banner = f"--- {quest_banner} ---"
            click.echo(f"    {quest_banner}")
    else:
        click.echo("    No active quests.")


def _display_lineage(recent_lineage):
    if recent_lineage:
        for entry in recent_lineage:
            parsed_details = json.loads(entry["details"]) if entry["details"] else {}
            action_type = (
                parsed_details.get("event_type", "unknown").replace("_", " ").title()
            )
            payload_details = parsed_details.get("payload", {})
            contributor = payload_details.get("contributor_id", "system")
            timestamp = payload_details.get("timestamp", entry["timestamp"])

            if action_type == "Trait Evolved":
                click.echo(
                    f"  ✨ [{timestamp}] {contributor} evolved {payload_details.get('trait_id')} to level {payload_details.get('new_level')}."
                )
            elif action_type == "Item Acquired":
                click.echo(
                    f"  🎒 [{timestamp}] {contributor} acquired {payload_details.get('quantity')} {payload_details.get('item_id')}(s)."
                )
            else:
                click.echo(f"  ⏳ [{timestamp}] {contributor} performed {action_type}.")
    else:
        click.echo("  No lineage entries found.")
    click.echo("\n")


@click.group(invoke_without_command=True)
def cli():
    """
    DevScape Ritual Engine CLI.
    """
    db_scroll.initialize_db()  # Ensure DB is initialized when CLI is invoked


@cli.command()
@click.option("--name", default="Steward", help="Name of the contributor.")
def status(name):
    """
    Displays the ceremonial dashboard.
    """
    click.echo(f"\n✦ Welcome, {name}, to the DevScape Ritual Status! ✦\n")

    # Load Configs
    onboarding_config = config_scroll.get_onboarding_config()
    prompts_config = config_scroll.get_prompts_config()
    click.echo("--- Config Scrolls 📜 ---")
    click.echo(f"  Title: {onboarding_config.get('title', 'N/A')}")
    click.echo(f"  Prompts: {len(prompts_config)} loaded\n")

    # Load State
    try:
        current_state = state_scroll.load_state()
        click.echo("--- Heart's Pulse (Current State) ❤️ ---")
        click.echo(
            f"  Player: {current_state['player']['name']} (Level {current_state['player']['level']}) Health: {current_state['player']['health']}"
        )

        click.echo("  Traits ✨:")
        _display_traits(current_state.get("traits", []))

        click.echo("  Quests 🗺️:")
        _display_quests(current_state.get("quests", []))

        planetary_mood = current_state["planetary_feedback"]["mood"]
        mood_glyph = (
            "😊"
            if planetary_mood == "calm"
            else (
                "😟"
                if planetary_mood == "unrest"
                else "🌟" if planetary_mood == "joy" else "❓"
            )
        )
        click.echo(f"  Planetary Mood {mood_glyph}: {planetary_mood}")
        click.echo(
            f"  Last Planetary Event: {current_state['planetary_feedback']['last_event']}\n"
        )

    except FileNotFoundError:
        click.echo(
            "Error: State file not found. Has the game state been initialized?\n"
        )
        current_state = {}
    except json.JSONDecodeError as e:
        click.echo(f"Error decoding state file: {e}\n")
        current_state = {}
    except Exception as e:
        click.echo(f"An unexpected error occurred while loading state: {e}\n")
        current_state = {}
    # Load Lineage
    recent_lineage = db_scroll.fetch_lineage(limit=5)
    click.echo("--- Lineage Archive (Recent Entries) 📜 ---")
    _display_lineage(recent_lineage)

    click.echo("✦ May your journey be guided by wisdom and your glyphs be true. ✦")


@cli.command()
@click.argument("trait_id")
@click.argument("level", type=int)
@click.option(
    "--contributor",
    default="Anonymous",
    help="Name of the contributor evolving the trait.",
)
def evolve(trait_id, level, contributor):
    """
    Evolves a specified trait to a new level.
    """
    click.echo(f"Attempting to evolve trait '{trait_id}' to level {level}...")
    payload = {
        "trait_id": trait_id,
        "new_level": level,
        "contributor_id": contributor,
        "description": f"Trait {trait_id} evolved to level {level}.",
    }
    event_bus.publish("trait_evolved", payload)
    click.echo(f"Trait '{trait_id}' evolved to level {level} and lineage inscribed.")


@cli.command()
@click.argument("mood")
@click.option(
    "--contributor",
    default="Anonymous",
    help="Name of the contributor logging the feedback.",
)
def feedback(mood, contributor):
    """
    Logs planetary mood feedback.
    """
    click.echo(f"Logging planetary mood: '{mood}'...")
    payload = {
        "mood": mood,
        "contributor_id": contributor,
        "timestamp": datetime.now().isoformat(),
        "description": f"Planetary mood set to {mood}.",
    }
    event_bus.publish("planetary_feedback", payload)
    click.echo(f"Planetary mood '{mood}' logged and lineage inscribed.")


@cli.group()
def quest():
    """
    Manage quest arcs.
    """


@quest.command("start")
@click.argument("quest_id")
@click.option(
    "--contributor",
    default="Anonymous",
    help="Name of the contributor starting the quest.",
)
def start_quest(quest_id, contributor):
    """
    Starts a new quest.
    """
    click.echo(f"Attempting to start quest '{quest_id}'...")
    payload = {
        "quest_id": quest_id,
        "status": "active",
        "progress": 0,
        "contributor_id": contributor,
        "description": f"Quest {quest_id} started.",
    }
    event_bus.publish("quest_started", payload)
    click.echo(f"Quest '{quest_id}' started and lineage inscribed.")


@quest.command("complete")
@click.argument("quest_id")
@click.option(
    "--contributor",
    default="Anonymous",
    help="Name of the contributor completing the quest.",
)
def complete_quest(quest_id, contributor):
    """
    Completes an active quest.
    """
    click.echo(f"Attempting to complete quest '{quest_id}'...")
    payload = {
        "quest_id": quest_id,
        "status": "completed",
        "progress": 100,
        "contributor_id": contributor,
        "description": f"Quest {quest_id} completed.",
    }
    event_bus.publish("quest_completed", payload)
    click.echo(f"Quest '{quest_id}' completed and lineage inscribed.")


@cli.command()
@click.argument("event_type")
@click.argument("payload", type=str)
def trigger_event(event_type, payload):
    """
    Triggers a custom event with a JSON payload.
    Example: devscape ritual trigger-event trait_evolved '{"trait_id": "wisdom", "new_level": 2, "contributor_id": "Brandon"}'
    """
    try:
        payload_dict = json.loads(payload)
        event_bus.publish(event_type, payload_dict)
        click.echo(
            f"Event '{event_type}' triggered successfully with payload: {payload_dict}"
        )
    except json.JSONDecodeError:
        click.echo("Error: Payload must be a valid JSON string.")
    except FileNotFoundError:
        click.echo("Error: State file not found.")
    except Exception as e:  # pylint: disable=broad-except
        click.echo(f"An unexpected error occurred: {e}")


# Event Bus Implementation
class EventBus:
    def __init__(self):
        self._listeners = {}

    def subscribe(self, event_name, listener):
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(listener)

    def publish(self, event_name, payload):
        if event_name in self._listeners:
            for listener in self._listeners[event_name]:
                listener(event_name, payload)


event_bus = EventBus()


def _update_state_planetary_feedback(current_state, payload):
    current_state["planetary_feedback"]["mood"] = payload.get("mood", "unknown")
    current_state["planetary_feedback"]["last_event"] = payload.get(
        "timestamp", datetime.now().isoformat()
    )
    current_state["planetary_feedback"]["events_log"].append(
        {
            "event_id": str(uuid.uuid4()),
            "timestamp": payload.get("timestamp", datetime.now().isoformat()),
            "description": payload.get("description", "Planetary mood updated."),
        }
    )


def _update_state_quest_completed(current_state, payload):
    quest_id = payload.get("quest_id")
    for q in current_state["quests"]:
        if q["quest_id"] == quest_id:
            q["status"] = payload.get("status", "completed")
            break


def _update_state_quest_started(current_state, payload):
    quest_id = payload.get("quest_id")
    quest_status = payload.get("status", "active")
    progress = payload.get("progress", 0)
    if not any(q["quest_id"] == quest_id for q in current_state["quests"]):
        current_state["quests"].append(
            {"quest_id": quest_id, "status": quest_status, "progress": progress}
        )


def _update_state_item_acquired(current_state, payload):
    item_id = payload.get("item_id")
    quantity = payload.get("quantity", 1)
    found = False
    for item in current_state["player"]["inventory"]:
        if item["item_id"] == item_id:
            item["quantity"] += quantity
            found = True
            break
    if not found:
        current_state["player"]["inventory"].append(
            {"item_id": item_id, "quantity": quantity}
        )


def _update_state_trait_evolved(current_state, payload):
    trait_id = payload.get("trait_id")
    new_level = payload.get("new_level")
    updated = False
    for trait in current_state["traits"]:
        if trait["trait_id"] == trait_id:
            trait["level"] = new_level
            trait["description"] = payload.get(
                "description", f"Trait {trait_id} evolved."
            )
            updated = True
            break
    if not updated:
        current_state["traits"].append(
            {
                "trait_id": trait_id,
                "level": new_level,
                "description": payload.get("description", f"Trait {trait_id} evolved."),
            }
        )


# --- Event Handlers ---

_STATE_UPDATE_HANDLERS = {
    "trait_evolved": _update_state_trait_evolved,
    "item_acquired": _update_state_item_acquired,
    "quest_started": _update_state_quest_started,
    "quest_completed": _update_state_quest_completed,
    "planetary_feedback": _update_state_planetary_feedback,
}


def handle_state_update(event_type_param, payload):
    current_state = state_scroll.load_state()
    handler = _STATE_UPDATE_HANDLERS.get(event_type_param)
    if handler:
        handler(current_state, payload)
    else:
        click.echo(
            f"Warning: No state update handler for event type: {event_type_param}"
        )

    state_scroll.save_state(current_state)
    click.echo(f"State updated for event: {event_type_param}")


def handle_lineage_recording(event_type_param, payload):
    contributor_id = payload.get("contributor_id", "system")
    details = json.dumps({"event_type": event_type_param, "payload": payload})
    db_scroll.record_lineage_event(contributor_id, event_type_param, details)
    click.echo(f"Lineage recorded for event: {event_type_param}")


# --- Subscribe Handlers to Events ---
# Core event types that trigger state updates and lineage recording
CORE_EVENT_TYPES = [
    "quest_started",
    "trait_evolved",
    "item_acquired",
    "quest_completed",
    "planetary_feedback",
]

for event_type in CORE_EVENT_TYPES:
    event_bus.subscribe(event_type, handle_state_update)
    event_bus.subscribe(event_type, handle_lineage_recording)

# Add more event subscriptions as needed


if __name__ == "__main__":
    cli()
