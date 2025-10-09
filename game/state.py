"""
state.py

Defines core game state classes and data structures.
"""

class GameState:
    """Represents the overall state of the game."""
    def __init__(self):
        pass

class LLMCharacter:
    """Represents the LLM-controlled character's state."""
    def __init__(self):
        self.mood = "neutral"
        self.traits = {}

class Player:
    """Represents the player character's state."""
    def __init__(self):
        pass

class World:

    """Represents the game world's state."""

    def __init__(self, name: str, locations: list = None):

        self.name = name

        self.locations = locations if locations is not None else []



    def __str__(self):

        return f"World: {self.name}, Locations: {len(self.locations)}"

class Location:

    """Represents a specific location in the game world."""

    def __init__(self, name: str, description: str = "", exits: dict = None):

        self.name = name

        self.description = description

        self.exits = exits if exits is not None else {}



    def __str__(self):

        return f"Location: {self.name}, Description: {self.description[:20]}..., Exits: {len(self.exits)}"

class Trait:
    """Represents a character trait."""
    def __init__(self, name, value):
        self.name = name
        self.value = value
