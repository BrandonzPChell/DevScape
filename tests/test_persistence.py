import os
import sqlite3
import tempfile
import unittest

from devscape import persistence


class TestPersistence(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)
        self.db_path = os.path.join(self.test_dir.name, "lineage.db")
        self.conn = persistence.init_lineage_db(self.db_path)

    def tearDown(self):
        if self.conn:
            self.conn.close()
        self.test_dir.cleanup()

    def test_save_and_load_json(self):
        """Test saving and loading a valid JSON file."""
        json_path = os.path.join(self.test_dir.name, "test.json")
        data = {"key": "value", "number": 123}
        persistence.save_json(data, json_path)
        loaded_data = persistence.load_json(json_path)
        self.assertEqual(data, loaded_data)

    def test_load_nonexistent_json(self):
        """Test loading a JSON file that does not exist."""
        json_path = os.path.join(self.test_dir.name, "nonexistent.json")
        loaded_data = persistence.load_json(json_path)
        self.assertEqual({}, loaded_data)

    def test_load_corrupt_json(self):
        """Test loading a corrupt JSON file."""
        json_path = os.path.join(self.test_dir.name, "corrupt.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write("INVALID JSON")  # Corrupt JSON
        loaded_data = persistence.load_json(json_path)
        self.assertEqual({}, loaded_data)

    def test_yaml_load(self):
        """Test loading a YAML file."""
        yaml_path = os.path.join(self.test_dir.name, "test.yml")
        yaml_content = "key: value\nnumber: 123"
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)
        loaded_data = persistence.load_yaml(yaml_path)
        self.assertEqual({"key": "value", "number": 123}, loaded_data)

    def test_load_nonexistent_yaml(self):
        """Test loading a YAML file that does not exist."""
        yaml_path = os.path.join(self.test_dir.name, "nonexistent.yml")
        loaded_data = persistence.load_yaml(yaml_path)
        self.assertEqual({}, loaded_data)

    def test_lineage_db_rituals(self):
        """Test the full lifecycle of SQLite lineage rituals."""
        # 1. Init DB (already done in setUp)
        self.assertIsInstance(self.conn, sqlite3.Connection)

        # 2. Write traits
        persistence.write_trait_log(self.conn, "courage", 10, "brandon")
        persistence.write_trait_log(self.conn, "focus", 5, "brandon")
        persistence.write_trait_log(
            self.conn, "courage", 11, "scribe"
        )  # Update courage

        # 3. Read latest traits
        latest_traits = persistence.read_latest_traits(self.conn)
        self.assertEqual(latest_traits["courage"], 11)  # Expect integer 11
        self.assertEqual(latest_traits["focus"], 5)  # Expect integer 5
        self.assertEqual(len(latest_traits), 2)


if __name__ == "__main__":
    unittest.main()
