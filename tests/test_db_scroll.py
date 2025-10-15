import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.devscape.db_scroll import (
    fetch_events,
    fetch_lineage,
    fetch_trait_evolution,
    initialize_db,
    record_game_event,
    record_trait_evolution,
)


class TestDbScroll(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test.db"
        self.schema_path = Path(__file__).parent.parent / "lineage.sql"

        self.db_patcher = patch("src.devscape.db_scroll.DB_FILE", self.db_path)
        self.schema_patcher = patch(
            "src.devscape.db_scroll.SCHEMA_FILE", self.schema_path
        )

        self.db_patcher.start()
        self.schema_patcher.start()

        initialize_db()
        self.conn = sqlite3.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.db_patcher.stop()
        self.schema_patcher.stop()
        self.tmpdir.cleanup()

    def test_record_game_event(self):
        record_game_event("test_event", "test_entity", '{"data": "test"}')
        c = self.conn.cursor()
        c.execute("SELECT * FROM events")
        event = c.fetchone()
        self.assertIsNotNone(event)
        self.assertEqual(event[1], "test_event")

    def test_record_trait_evolution(self):
        record_trait_evolution("strength", 12, "tester", 10, '{"reason": "level up"}')
        c = self.conn.cursor()
        c.execute("SELECT * FROM traits_evolution")
        evolution = c.fetchone()
        self.assertIsNotNone(evolution)
        self.assertEqual(evolution[1], "strength")
        self.assertEqual(evolution[4], 12)

    def test_fetch_lineage(self):
        self.conn.execute(
            "INSERT INTO lineage (contributor_id, action_type, details) VALUES (?, ?, ?)",
            ("tester", "test_action", "details"),
        )
        self.conn.commit()
        lineage = fetch_lineage()
        self.assertEqual(len(lineage), 1)
        self.assertEqual(lineage[0]["contributor_id"], "tester")

    def test_fetch_events(self):
        record_game_event("test_event", "test_entity", '{"data": "test"}')
        events = fetch_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "test_event")

    def test_fetch_trait_evolution(self):
        record_trait_evolution("strength", 12, "tester", 10, '{"reason": "level up"}')
        record_trait_evolution("magic", 5, "tester", 4, '{"reason": "new spell"}')

        # Fetch all
        evolutions = fetch_trait_evolution()
        self.assertEqual(len(evolutions), 2)

        # Fetch by trait_id
        strength_evolutions = fetch_trait_evolution(trait_id="strength")
        self.assertEqual(len(strength_evolutions), 1)
        self.assertEqual(strength_evolutions[0]["new_level"], 12)


if __name__ == "__main__":
    unittest.main()
