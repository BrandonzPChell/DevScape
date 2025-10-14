import json
import sqlite3
from datetime import datetime


def sync_traits_to_db(json_path, db_path, contributor="Brandon"):
    """
    Ensures traits.json and lineage.db mirror each other.
    Every trait evolution in JSON is logged in SQLite with a timestamp and contributor.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            traits = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    timestamp = datetime.utcnow().isoformat()

    for trait, value in traits.items():
        # For structured values (lists, dicts), store them as a JSON string
        value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        c.execute(
            "INSERT INTO trait_log (trait, value, timestamp, contributor) VALUES (?, ?, ?, ?)",
            (trait, value_str, timestamp, contributor),
        )

    conn.commit()
    conn.close()
    print(f"Successfully synced traits from {json_path} to {db_path}")


def sync_db_to_traits(db_path, json_path):
    """
    Regenerates a JSON trait file from the latest entries in the SQLite lineage log.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name

    # This query selects the most recent record for each trait
    query = """
    SELECT trait, value
    FROM trait_log
    WHERE id IN (
        SELECT MAX(id)
        FROM trait_log
        GROUP BY trait
    )
    """
    try:
        c = conn.cursor()
        c.execute(query)
        rows = c.fetchall()
    finally:
        conn.close()

    if not rows:
        print(f"Warning: No records found in {db_path} to sync to {json_path}")
        return

    reconstructed_traits = {}
    for row in rows:
        trait = row["trait"]
        value_str = row["value"]
        try:
            # Attempt to parse the value back into a Python object
            reconstructed_traits[trait] = json.loads(value_str)
        except (json.JSONDecodeError, TypeError):
            # If it's not a valid JSON string, just use the string value
            reconstructed_traits[trait] = value_str

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(reconstructed_traits, f, indent=2, sort_keys=True)
        print(f"Successfully regenerated {json_path} from {db_path}")
    except IOError as e:
        print(f"Error writing to {json_path}: {e}")
