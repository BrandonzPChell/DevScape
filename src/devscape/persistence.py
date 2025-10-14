import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, Tuple

import yaml

# --- JSON Rituals ---


def load_json(path: str) -> Dict[str, Any]:
    """Loads a JSON file from the given path."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Could not find {path}. Returning empty dictionary.")
        return {}
    except json.JSONDecodeError:
        print(
            f"Warning: Could not decode JSON from {path}. Returning empty dictionary."
        )
        return {}


def save_json(data: Dict[str, Any], path: str) -> None:
    """Saves a dictionary to a JSON file at the given path."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


# --- YAML Rituals ---


def load_yaml(path: str) -> Dict[str, Any]:
    """Loads a YAML file from the given path."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: Could not find {path}. Returning empty dictionary.")
        return {}


# --- SQLite Lineage Rituals ---


def init_lineage_db(path: str) -> sqlite3.Connection:
    """Initializes the lineage database and returns a connection."""
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS trait_log (
        id INTEGER PRIMARY KEY,
        trait TEXT NOT NULL,
        value TEXT,
        timestamp TEXT NOT NULL,
        contributor TEXT
    )"""
    )
    conn.commit()
    return conn


def write_trait_log(
    conn: sqlite3.Connection, trait: str, value: Any, contributor: str
) -> None:
    """Writes a single trait change to the lineage log."""
    timestamp = datetime.utcnow().isoformat()
    value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
    c = conn.cursor()
    c.execute(
        "INSERT INTO trait_log (trait, value, timestamp, contributor) VALUES (?, ?, ?, ?)",
        (trait, value_str, timestamp, contributor),
    )
    conn.commit()


def read_latest_traits(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Reads the latest value for each trait from the lineage log."""
    conn.row_factory = sqlite3.Row
    query = """
    SELECT trait, value
    FROM trait_log
    WHERE id IN (
        SELECT MAX(id)
        FROM trait_log
        GROUP BY trait
    )
    """
    c = conn.cursor()
    c.execute(query)
    rows = c.fetchall()

    reconstructed_traits = {}
    for row in rows:
        trait = row["trait"]
        value_str = row["value"]
        try:
            reconstructed_traits[trait] = json.loads(value_str)
        except (json.JSONDecodeError, TypeError):
            reconstructed_traits[trait] = value_str
    return reconstructed_traits


# --- Validation Rituals ---


def validate_and_quarantine(
    data: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Validates a dictionary, returning valid and quarantined items."""
    valid = {}
    quarantined = {}
    for key, value in data.items():
        if isinstance(value, (str, int, float, bool, list, dict)):
            valid[key] = value
        else:
            quarantined[key] = value
    return valid, quarantined
