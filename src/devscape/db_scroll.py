import sqlite3
from pathlib import Path
from typing import Optional

DB_FILE = Path(__file__).parent.parent.parent / "lineage.db"
SCHEMA_FILE = Path(__file__).parent.parent.parent / "lineage.sql"


def _get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    """
    Initializes the database schema from lineage.sql.
    """
    conn = _get_db_connection()
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_script = f.read()
    conn.executescript(schema_script)
    conn.close()


def record_lineage_event(
    contributor_id: str, action_type: str, details: Optional[str] = None
):
    """
    Records an event in the lineage table.
    """
    conn = _get_db_connection()
    conn.execute(
        "INSERT INTO lineage (contributor_id, action_type, details) VALUES (?, ?, ?)",
        (contributor_id, action_type, details),
    )
    conn.commit()
    conn.close()


def record_game_event(
    event_type: str,
    related_entity_id: Optional[str] = None,
    details: Optional[str] = None,
):
    """
    Records an event in the events table.
    """
    conn = _get_db_connection()
    conn.execute(
        "INSERT INTO events (event_type, related_entity_id, details) VALUES (?, ?, ?)",
        (event_type, related_entity_id, details),
    )
    conn.commit()
    conn.close()


def record_trait_evolution(
    trait_id: str,
    new_level: int,
    contributor_id: Optional[str] = None,
    old_level: Optional[int] = None,
    details: Optional[str] = None,
):
    """
    Records a trait evolution in the traits_evolution table.
    """
    conn = _get_db_connection()
    conn.execute(
        "INSERT INTO traits_evolution (trait_id, contributor_id, old_level, new_level, details) VALUES (?, ?, ?, ?, ?)",
        (trait_id, contributor_id, old_level, new_level, details),
    )
    conn.commit()
    conn.close()


def fetch_lineage(limit: int = 100):
    """
    Fetches recent lineage events.
    """
    conn = _get_db_connection()
    cursor = conn.execute(
        "SELECT * FROM lineage ORDER BY timestamp DESC LIMIT ?", (limit,)
    )
    lineage_data = cursor.fetchall()
    conn.close()
    return [dict(row) for row in lineage_data]


def fetch_events(limit: int = 100):
    """
    Fetches recent game events.
    """
    conn = _get_db_connection()
    cursor = conn.execute(
        "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,)
    )
    events_data = cursor.fetchall()
    conn.close()
    return [dict(row) for row in events_data]


def fetch_trait_evolution(trait_id: Optional[str] = None, limit: int = 100):
    """
    Fetches trait evolution history, optionally for a specific trait.
    """
    conn = _get_db_connection()
    if trait_id:
        cursor = conn.execute(
            "SELECT * FROM traits_evolution WHERE trait_id = ? ORDER BY timestamp DESC LIMIT ?",
            (
                trait_id,
                limit,
            ),
        )
    else:
        cursor = conn.execute(
            "SELECT * FROM traits_evolution ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
    trait_data = cursor.fetchall()
    conn.close()
    return [dict(row) for row in trait_data]
