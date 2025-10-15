import json

import yaml


def invoke_onboarding_scroll(yaml_path="onboarding.yml", json_path="onboarding.json"):
    """
    Converts the human-readable onboarding scroll (YAML) into a
    machine-legible format (JSON).
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            print(f"Reading ceremonial scroll from {yaml_path}...")
            onboarding = yaml.safe_load(f)

        with open(json_path, "w", encoding="utf-8") as f:
            print(f"Inscribing dashboard overlay to {json_path}...")
            json.dump(onboarding, f, indent=2)

        print("Invocation complete.")
    except FileNotFoundError as e:
        print(f"Error: Could not find a required scroll. {e}")
    except Exception as e:
        print(f"An unexpected error occurred during the invocation: {e}")
