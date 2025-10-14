from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def load_config(filename: str):
    """
    Loads a YAML configuration file from the config directory.
    """
    filepath = CONFIG_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_onboarding_config():
    """
    Returns the onboarding configuration.
    """
    return load_config("onboarding.yml")


def get_prompts_config():
    """
    Returns the prompts configuration.
    """
    return load_config("prompts.yml")
