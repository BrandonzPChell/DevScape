import json
import sqlite3


def validate_traits(json_path, quarantine_path):
    """
    Scans a JSON file for invalid entries and isolates them for review.
    Valid types are string, int, float, and bool. Others are quarantined.
    Note: This is a destructive operation on the source json_path.
    """
    print(f"Validating {json_path}...")
    valid_write_successful = False
    quarantined = {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            traits = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading {json_path}: {e}")
        return

    valid = {}

    for trait, value in traits.items():
        if isinstance(value, (str, int, float, bool)):
            valid[trait] = value
        else:
            print(f"  - Quarantining trait '{trait}' (type: {type(value).__name__}).")
            quarantined[trait] = value

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(valid, f, indent=2, sort_keys=True)
        print(f"Wrote valid traits back to {json_path}.")
        valid_write_successful = True
    except IOError as e:
        print(f"Error writing validation results: {e}")
        valid_write_successful = False

    if valid_write_successful and quarantined:
        try:
            with open(quarantine_path, "w", encoding="utf-8") as f:
                json.dump(quarantined, f, indent=2, sort_keys=True)
            print(f"Wrote quarantined traits to {quarantine_path}.")
        except IOError as e:
            print(f"Error writing validation results: {e}")
    elif valid_write_successful and not quarantined:
        print("No traits were quarantined.")


def recover_traits_from_db(db_path, json_path):
    """
    Regenerates a JSON trait file from the latest entries in the SQLite lineage log.
    This is a new name for the previously verified sync_db_to_traits ritual.
    """
    print(f"Recovering latest traits from {db_path} into {json_path}...")
    conn = sqlite3.connect(db_path)
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
    try:
        c = conn.cursor()
        c.execute(query)
        rows = c.fetchall()
    finally:
        conn.close()

    if not rows:
        print(f"Warning: No records found in {db_path}.")
        return

    reconstructed_traits = {}
    for row in rows:
        trait = row["trait"]
        value_str = row["value"]
        try:
            reconstructed_traits[trait] = json.loads(value_str)
        except (json.JSONDecodeError, TypeError):
            reconstructed_traits[trait] = value_str

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(reconstructed_traits, f, indent=2, sort_keys=True)
        print(f"Successfully recovered traits to {json_path}.")
    except IOError as e:
        print(f"Error writing to {json_path}: {e}")


def recover_and_validate_traits(db_path, json_path, quarantine_path):
    """
    A combo ritual that first recovers the latest traits from the database,
    then validates the result, quarantining any malformed entries.
    """
    print("--- Beginning Recovery + Validation Combo Ritual ---")
    # Step 1: Recover traits from the ancestral archive
    recover_traits_from_db(db_path, json_path)

    # Step 2: Validate and purify the newly recovered scroll
    validate_traits(json_path, quarantine_path)
    print("--- Combo Ritual Complete ---")
