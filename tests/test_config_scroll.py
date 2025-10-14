import unittest
from unittest.mock import mock_open, patch

from src.devscape.config_scroll import (
    get_onboarding_config,
    get_prompts_config,
    load_config,
)


class TestConfigScroll(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data="key: value")
    @patch("yaml.safe_load")
    def test_load_config(self, mock_safe_load, mock_open_file):
        """
        Tests that load_config opens the correct file and calls yaml.safe_load.
        """
        expected_dict = {"key": "value"}
        mock_safe_load.return_value = expected_dict

        result = load_config("anyfile.yml")

        mock_open_file.assert_called_once()
        mock_safe_load.assert_called_once()
        self.assertEqual(result, expected_dict)

    @patch("src.devscape.config_scroll.load_config")
    def test_get_onboarding_config(self, mock_load_config):
        """
        Tests that get_onboarding_config calls load_config with 'onboarding.yml'.
        """
        expected_config = {"onboarding": "config"}
        mock_load_config.return_value = expected_config

        result = get_onboarding_config()

        mock_load_config.assert_called_with("onboarding.yml")
        self.assertEqual(result, expected_config)

    @patch("src.devscape.config_scroll.load_config")
    def test_get_prompts_config(self, mock_load_config):
        """
        Tests that get_prompts_config calls load_config with 'prompts.yml'.
        """
        expected_config = {"prompts": "config"}
        mock_load_config.return_value = expected_config

        result = get_prompts_config()

        mock_load_config.assert_called_with("prompts.yml")
        self.assertEqual(result, expected_config)


if __name__ == "__main__":
    unittest.main()
