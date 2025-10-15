import json

import pytest

from devscape.badges import CovenantBadge, CoverageBadge, LineageBadge


class TestCovenantBadge:
    def test_status_passing(self):
        badge = CovenantBadge(contributing_ok=True, conduct_ok=True)
        assert badge.status == "passing"

    def test_status_failing(self):
        badge = CovenantBadge(contributing_ok=False, conduct_ok=True)
        assert badge.status == "failing"

    def test_color_passing(self):
        badge = CovenantBadge(contributing_ok=True, conduct_ok=True)
        assert badge.color == "brightgreen"

    def test_color_failing(self):
        badge = CovenantBadge(contributing_ok=False, conduct_ok=True)
        assert badge.color == "red"

    def test_to_markdown(self):
        badge = CovenantBadge(contributing_ok=True, conduct_ok=True)
        assert badge.to_markdown() == "![Covenants](covenants-passing-brightgreen)"

    def test_to_json_str(self):
        badge = CovenantBadge(contributing_ok=True, conduct_ok=True)
        expected_json = {
            "type": "covenants",
            "status": "passing",
            "color": "brightgreen",
            "markdown": "![Covenants](covenants-passing-brightgreen)",
        }
        assert badge.to_json_str() == json.dumps(expected_json, indent=2)


class TestCoverageBadge:
    @pytest.mark.parametrize(
        "coverage, expected_color",
        [
            (90, "brightgreen"),
            (85, "brightgreen"),
            (80, "yellow"),
            (70, "yellow"),
            (60, "orange"),
            (50, "orange"),
            (40, "red"),
        ],
    )
    def test_color(self, coverage, expected_color):
        badge = CoverageBadge(coverage_percent=coverage)
        assert badge.color == expected_color

    def test_to_markdown(self):
        badge = CoverageBadge(coverage_percent=85)
        assert (
            badge.to_markdown()
            == "![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)"
        )

    def test_to_json_str(self):
        badge = CoverageBadge(coverage_percent=85)
        expected_json = {
            "type": "coverage",
            "value": 85,
            "color": "brightgreen",
            "markdown": "![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)",
        }
        assert badge.to_json_str() == json.dumps(expected_json, indent=2)


class TestLineageBadge:
    def test_color_with_entries(self):
        badge = LineageBadge(depth=10)
        assert badge.color == "blue"

    def test_color_no_entries(self):
        badge = LineageBadge(depth=0)
        assert badge.color == "lightgrey"

    def test_to_markdown(self):
        badge = LineageBadge(depth=10)
        assert (
            badge.to_markdown()
            == "![Lineage](https://img.shields.io/badge/lineage-10_entries-blue)"
        )

    def test_to_json_str(self):
        badge = LineageBadge(depth=10)
        expected_json = {
            "type": "lineage",
            "entries": 10,
            "color": "blue",
            "markdown": "![Lineage](https://img.shields.io/badge/lineage-10_entries-blue)",
        }
        assert badge.to_json_str() == json.dumps(expected_json, indent=2)
