"""
badges.py

Defines the Badge class for generating markdown and JSON for badges.
"""

import json
from dataclasses import dataclass


@dataclass
class CovenantBadge:
    """Badge for covenant status."""

    contributing_ok: bool
    conduct_ok: bool

    @property
    def status(self) -> str:
        """Returns the status of the badge."""
        return "passing" if self.contributing_ok and self.conduct_ok else "failing"

    @property
    def color(self) -> str:
        """Returns the color of the badge."""
        return "brightgreen" if self.status == "passing" else "red"

    def to_markdown(self) -> str:
        """Returns the markdown representation of the badge."""
        return f"![Covenants](covenants-{self.status}-{self.color})"

    def to_json_str(self) -> str:
        """Returns the JSON string representation of the badge."""
        data = {
            "type": "covenants",
            "status": self.status,
            "color": self.color,
            "markdown": self.to_markdown(),
        }
        return json.dumps(data, indent=2)


@dataclass
class CoverageBadge:
    """Badge for code coverage."""

    coverage_percent: int

    @property
    def color(self) -> str:
        """Returns the color of the badge."""
        if self.coverage_percent >= 85:
            return "brightgreen"
        if self.coverage_percent >= 70:
            return "yellow"
        if self.coverage_percent >= 50:
            return "orange"
        return "red"

    def to_markdown(self) -> str:
        """Returns the markdown representation of the badge."""
        return (
            f"![Coverage](https://img.shields.io/badge/coverage-"
            f"{self.coverage_percent}%25-{self.color})"
        )

    def to_json_str(self) -> str:
        """Returns the JSON string representation of the badge."""
        data = {
            "type": "coverage",
            "value": self.coverage_percent,
            "color": self.color,
            "markdown": self.to_markdown(),
        }
        return json.dumps(data, indent=2)


@dataclass
class LineageBadge:
    """Badge for lineage depth."""

    depth: int

    @property
    def color(self) -> str:
        """Returns the color of the badge."""
        return "blue" if self.depth > 0 else "lightgrey"

    def to_markdown(self) -> str:
        """Returns the markdown representation of the badge."""
        return f"![Lineage](https://img.shields.io/badge/lineage-{self.depth}_entries-{self.color})"

    def to_json_str(self) -> str:
        """Returns the JSON string representation of the badge."""
        data = {
            "type": "lineage",
            "entries": self.depth,
            "color": self.color,
            "markdown": self.to_markdown(),
        }
        return json.dumps(data, indent=2)
