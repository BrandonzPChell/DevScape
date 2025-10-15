import json
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.devscape.validation_rituals import (
    recover_and_validate_traits,
    recover_traits_from_db,
    validate_traits,
)


class TestValidationRituals(unittest.TestCase):
    def test_recover_traits_from_db(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            json_path = Path(tmpdir) / "test.json"

            # Create and populate a dummy database
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute(
                "CREATE TABLE trait_log (id INTEGER PRIMARY KEY, trait TEXT, value TEXT)"
            )
            c.execute(
                "INSERT INTO trait_log (trait, value) VALUES (?, ?)", ("strength", "10")
            )
            c.execute(
                "INSERT INTO trait_log (trait, value) VALUES (?, ?)", ("magic", "15")
            )
            c.execute(
                "INSERT INTO trait_log (trait, value) VALUES (?, ?)", ("strength", "12")
            )  # newer value
            conn.commit()
            conn.close()

            recover_traits_from_db(db_path, json_path)

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(data, {"strength": 12, "magic": 15})

    @patch("src.devscape.validation_rituals.validate_traits")
    @patch("src.devscape.validation_rituals.recover_traits_from_db")
    def test_recover_and_validate_traits(self, mock_recover, mock_validate):
        db_path = "dummy.db"
        json_path = "dummy.json"
        quarantine_path = "dummy_quarantine.json"

        recover_and_validate_traits(db_path, json_path, quarantine_path)

        mock_recover.assert_called_once_with(db_path, json_path)
        mock_validate.assert_called_once_with(json_path, quarantine_path)

    def test_validate_traits(self):
        with TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "traits.json"
            quarantine_path = Path(tmpdir) / "quarantine.json"

            # Test data with valid and invalid types
            test_data = {
                "valid_str": "hello",
                "valid_int": 123,
                "valid_float": 1.23,
                "valid_bool": True,
                "invalid_list": [1, 2],
                "invalid_dict": {"a": 1},
            }

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            validate_traits(json_path, quarantine_path)

            # Check the original file was modified
            with open(json_path, "r", encoding="utf-8") as f:
                valid_data = json.load(f)
            self.assertEqual(
                valid_data,
                {
                    "valid_str": "hello",
                    "valid_int": 123,
                    "valid_float": 1.23,
                    "valid_bool": True,
                },
            )

            # Check the quarantine file was created
            with open(quarantine_path, "r", encoding="utf-8") as f:
                quarantined_data = json.load(f)
            self.assertEqual(
                quarantined_data, {"invalid_list": [1, 2], "invalid_dict": {"a": 1}}
            )


if __name__ == "__main__":
    unittest.main()
