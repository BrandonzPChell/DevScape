"""
main.py

Entry point for the game. Handles initialization, event loop, rendering, and
integration with pixel art rendering and dialogue systems.
"""

# pylint: disable=E1101

import json
import logging
import os
import subprocess
import time
from typing import List, Tuple
from unittest.mock import MagicMock

import pygame

from devscape import constants
from devscape.badges import CovenantBadge, CoverageBadge, LineageBadge
from devscape.maps import GAME_MAP, TILE_ART_MAP
from devscape.ollama_ai import get_llm_move
from devscape.rendering import (
    draw_chat_bubble,
    render_dashboard_content,
    render_pixel_art,
)
from devscape.state import LLMCharacter
from devscape.state_manager import StateManager

__version__ = "0.1.0"

# Game constants


# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


class Game:  # pylint: disable=R0904
    """Core class to manage game state, logic, and rendering."""

    def __init__(self):
        """Initializes the game, screen, entities, and timers."""
        pygame.init()
        pygame.font.init()  # Initialize font module
        self.screen = pygame.display.set_mode(
            (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        )
        pygame.display.set_caption("RuneScape-like Pixel Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)  # Font for chat
        self.running = True

        # Game state

        self.map_width_pixels = len(GAME_MAP[0]) * constants.TILE_SIZE
        self.map_height_pixels = len(GAME_MAP) * constants.TILE_SIZE

        self.state_manager = StateManager()
        self.player = self.state_manager.game_state.player
        self.llm_character_id = None
        for entity in self.state_manager.game_state.entities.values():
            if isinstance(entity, LLMCharacter):
                self.llm_character_id = entity.id
                break
        if self.llm_character_id is None:
            logging.warning("No LLMCharacter found in initial entities.")

        self.entities = list(self.state_manager.game_state.entities.values())

        self.ollama_client = MagicMock()  # Instantiate OllamaClient

        self.llm_move_timer = 0
        self.llm_move_interval = 2000  # in milliseconds

        self.camera_offset_x = 0
        self.camera_offset_y = 0

        self.should_speak = True  # New attribute for conditional speech
        self.planetary_mood = 0.0  # Initialize planetary mood

        self.timeline_log = []  # list of {timestamp, mood, traits}
        self.event_log = []  # Initialize event_log
        self.chat_history: List[Tuple[str, str]] = []
        self.chat_input: str = ""
        self.in_chat_mode: bool = False

    def show_chat_bubble(self, entity, text: str, duration: int = 3000):
        """Assigns text and timing information to an entity's chat bubble."""
        entity.bubble_text = text
        entity.bubble_start_time = pygame.time.get_ticks()
        entity.bubble_duration = duration
        entity.bubble_expires = pygame.time.get_ticks() + max(0, duration)

    def handle_keydown(self, key):
        """
        Simulates a keydown event for testing purposes, directly processing the key.
        """
        if self.state_manager.get_game_state().in_chat_mode:
            self._handle_chat_mode_keydown(key)
        else:
            if key == pygame.K_t:
                self.state_manager.get_game_state().in_chat_mode = True
                self.state_manager.get_game_state().chat_buffer = ""
            elif key == pygame.K_UP:
                self.state_manager.player_manager.move_player(0, -1)
            elif key == pygame.K_DOWN:
                self.state_manager.player_manager.move_player(0, 1)
            elif key == pygame.K_LEFT:
                self.state_manager.player_manager.move_player(-1, 0)
            elif key == pygame.K_RIGHT:
                self.state_manager.player_manager.move_player(1, 0)

    def handle_text_input(self, text):
        """
        Simulates a text input event for testing purposes.
        """
        if self.state_manager.get_game_state().in_chat_mode:
            self.state_manager.get_game_state().chat_buffer += text

    def send_player_message(self, message: str):
        """Handles sending a player message to the AI and displaying responses."""
        logging.info("Player message sent: '%s'", message)
        # Show player’s bubble
        self.show_chat_bubble(self.player, message)

        # Send to AI spirit
        try:
            reply = self.ollama_client.send_message(message)
            logging.info("AI replied: '%s'", reply)
        except Exception as e:  # pylint: disable=W0718
            logging.error("Error during AI interaction: %s", e, exc_info=True)
            reply = "I'm having trouble responding right now..."

        # Show AI’s bubble
        self.show_chat_bubble(
            self.state_manager.get_game_state().entities.get(self.llm_character_id),
            reply,
        )

    def _handle_chat_mode_keydown(self, key):
        if key == pygame.K_RETURN:
            if self.state_manager.get_game_state().chat_buffer.strip():
                self.send_player_message(
                    self.state_manager.get_game_state().chat_buffer
                )
            self.state_manager.get_game_state().chat_buffer = ""
            self.state_manager.get_game_state().in_chat_mode = False
        elif key == pygame.K_ESCAPE:
            self.state_manager.get_game_state().chat_buffer = ""
            self.state_manager.get_game_state().in_chat_mode = False
        elif key == pygame.K_BACKSPACE:
            self.state_manager.get_game_state().chat_buffer = (
                self.state_manager.get_game_state().chat_buffer[:-1]
            )
        # Other keys are handled by TEXTINPUT

    def _handle_gameplay_keydown(self, key):
        if key == pygame.K_t:
            self.state_manager.get_game_state().in_chat_mode = True
            self.state_manager.get_game_state().chat_buffer = ""
        elif key == pygame.K_UP:
            self.state_manager.player_manager.move_player(0, -1)
        elif key == pygame.K_DOWN:
            self.state_manager.player_manager.move_player(0, 1)
        elif key == pygame.K_LEFT:
            self.state_manager.player_manager.move_player(-1, 0)
            self.state_manager.player_manager.move_player(1, 0)

    def handle_events(self):
        """Handles all user input and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if self.state_manager.get_game_state().in_chat_mode:
                    self._handle_chat_mode_keydown(event.key)
                else:
                    self._handle_gameplay_keydown(event.key)
            elif (
                event.type == pygame.TEXTINPUT
                and self.state_manager.get_game_state().in_chat_mode
            ):

                # Collect typed characters into buffer

                self.state_manager.get_game_state().chat_buffer += event.text

    def _expire_chat_bubbles(self, now):
        """Expires chat bubbles for all entities."""
        for entity in self.entities:
            if (
                hasattr(entity, "bubble_text")
                and entity.bubble_text
                and hasattr(entity, "bubble_expires")
                and entity.bubble_expires <= now
            ):
                entity.bubble_text = ""
                entity.bubble_start_time = 0
                entity.bubble_duration = 0
                entity.bubble_expires = 0

    def update(self, dt: int):
        """Updates the state of game objects, including AI and dialogue."""
        now = pygame.time.get_ticks()

        # Update entities list from state manager
        self.entities = list(self.state_manager.get_all_entities().values())

        self._expire_chat_bubbles(now)

        self._update_camera()

        self._evolve_traits(dt)

        self._update_timeline_log()

        dialogue = self._update_llm_move(dt)
        if self.should_speak and dialogue:
            self.show_chat_bubble(
                self.state_manager.get_game_state().entities.get(self.llm_character_id),
                dialogue,
            )

    def _update_llm_move(self, dt: int) -> str | None:
        """Updates the LLM character's move and returns any dialogue."""
        self.llm_move_timer += dt

        move_delta = (0, 0)
        dialogue = None

        if self.llm_move_timer >= self.llm_move_interval:
            self.llm_move_timer -= self.llm_move_interval
            try:
                llm_char = self.state_manager.get_game_state().entities.get(
                    self.llm_character_id
                )
                player = self.state_manager.game_state.player
                move_delta, dialogue = get_llm_move(
                    player.x,
                    player.y,
                    llm_char.x,
                    llm_char.y,
                    GAME_MAP,
                    llm_char.mood,
                )
                logging.debug("LLM: %s, %s", move_delta, dialogue)
            except Exception as e:  # pylint: disable=W0718
                logging.error("Error getting LLM move: %s", e, exc_info=True)
                move_delta = (0, 0)
                dialogue = None
                if self.should_speak:
                    self.state_manager.get_game_state().entities.get(
                        self.llm_character_id
                    ).bubble_text = None

            if move_delta == (0, 0) and not self.should_speak:
                mood = getattr(
                    self.state_manager.get_game_state().entities.get(
                        self.llm_character_id
                    ),
                    "mood",
                    "neutral",
                )
                indicators = {
                    "neutral": "...",
                    "tired": "zzz",
                    "angry": "—",
                    "happy": "♪",
                }
                indicator = indicators.get(mood, "...")
                print(
                    f"Calling show_chat_bubble for silent indicator with mood: {mood}"
                )
                self.show_chat_bubble(
                    self.state_manager.get_game_state().entities.get(
                        self.llm_character_id
                    ),
                    indicator,
                    duration=1000,
                )
            else:
                dx, dy = move_delta
                llm_char = self.state_manager.get_game_state().entities.get(
                    self.llm_character_id
                )
                new_llm_x, new_llm_y = (
                    int(llm_char.x) + dx,
                    int(llm_char.y) + dy,
                )
                if (
                    0 <= new_llm_y < len(GAME_MAP)
                    and 0 <= new_llm_x < len(GAME_MAP[0])
                    and GAME_MAP[new_llm_y][new_llm_x] != "W"
                ):
                    llm_char.x, llm_char.y = new_llm_x, new_llm_y
        return dialogue

    def _update_camera(self):
        """Updates the camera position to center on the player and clamps it to the map boundaries."""
        player = self.state_manager.game_state.player
        self.camera_offset_x = (
            constants.SCREEN_WIDTH // 2 - player.x * constants.TILE_SIZE
        )
        self.camera_offset_y = (
            constants.SCREEN_HEIGHT // 2 - player.y * constants.TILE_SIZE
        )

        # Clamp camera to map boundaries
        self.camera_offset_x = min(self.camera_offset_x, 0)
        self.camera_offset_y = min(self.camera_offset_y, 0)
        self.camera_offset_x = max(
            self.camera_offset_x, constants.SCREEN_WIDTH - self.map_width_pixels
        )
        self.camera_offset_y = max(
            self.camera_offset_y, constants.SCREEN_HEIGHT - self.map_height_pixels
        )

    def _evolve_traits(self, dt: int):
        """Evolves the LLM character's traits based on planetary mood and time."""
        llm_char = self.state_manager.get_game_state().entities.get(
            self.llm_character_id
        )
        if hasattr(llm_char, "traits"):
            mood_value = getattr(self, "planetary_mood", 0.0)
            mood_factor = max(0.0, 1.0 + mood_value)

            base_evolution_rate = 0.1  # per second

            for trait_name, current_value in llm_char.traits.items():
                if trait_name == "patience":
                    change = base_evolution_rate * (dt / 1000) * mood_factor
                    print(
                        f"DEBUG: dt={dt}, mood_factor={mood_factor}, "
                        f"current_value={current_value}, change={change}"
                    )
                    llm_char.traits[trait_name] = current_value + change

    def _update_timeline_log(self):
        """Appends a snapshot of the current state to the timeline log."""
        llm_char = self.state_manager.get_game_state().entities.get(
            self.llm_character_id
        )
        snapshot = {
            "timestamp": time.time(),
            "mood": getattr(llm_char, "mood", "neutral"),
            "traits": dict(getattr(llm_char, "traits", {})),  # copy
        }
        self.timeline_log.append(snapshot)

    def render(self):
        """Draws all game objects to the screen."""
        self.screen.fill(BLACK)

        # Draw the map
        for row_idx, row in enumerate(GAME_MAP):
            for col_idx, tile_char in enumerate(row):
                tile_art = TILE_ART_MAP.get(tile_char)
                if tile_art:
                    tile_screen_x = col_idx * constants.TILE_SIZE + self.camera_offset_x
                    tile_screen_y = row_idx * constants.TILE_SIZE + self.camera_offset_y
                    # Cull tiles that are off-screen
                    if (
                        -constants.TILE_SIZE < tile_screen_x < constants.SCREEN_WIDTH
                        and -constants.TILE_SIZE
                        < tile_screen_y
                        < constants.SCREEN_HEIGHT
                    ):
                        render_pixel_art(
                            self.screen,
                            tile_art,
                            pygame.Rect(
                                tile_screen_x,
                                tile_screen_y,
                                constants.TILE_SIZE,
                                constants.TILE_SIZE,
                            ),
                        )

                # Draw entities and their chat bubbles
                for entity in [
                    e
                    for e in list(self.state_manager.get_all_entities().values())
                    if e.entity_type != constants.ENTITY_TYPES["ITEM"]
                ]:
                    entity_screen_x = (
                        entity.x * constants.TILE_SIZE + self.camera_offset_x
                    )
                    entity_screen_y = (
                        entity.y * constants.TILE_SIZE + self.camera_offset_y
                    )
                    render_pixel_art(
                        self.screen,
                        entity.art,
                        pygame.Rect(
                            entity_screen_x,
                            entity_screen_y,
                            constants.TILE_SIZE,
                            constants.TILE_SIZE,
                        ),
                    )

                    # Draw chat bubble if entity has text
                    if entity.bubble_text:
                        draw_chat_bubble(
                            self.screen,
                            entity.bubble_text,
                            (
                                entity_screen_x + constants.TILE_SIZE // 2,
                                entity_screen_y - 10,
                            ),
                            self.font,
                        )  # Draw chat input box if typing
        if self.in_chat_mode:
            input_box_rect = pygame.Rect(
                50, constants.SCREEN_HEIGHT - 50, constants.SCREEN_WIDTH - 100, 40
            )
            pygame.draw.rect(self.screen, WHITE, input_box_rect, border_radius=5)
            pygame.draw.rect(self.screen, BLACK, input_box_rect, 2, border_radius=5)
            input_text_surface = self.font.render(
                self.state_manager.get_game_state().chat_buffer + "|", True, BLACK
            )
            self.screen.blit(
                input_text_surface, (input_box_rect.x + 5, input_box_rect.y + 10)
            )

        pygame.display.flip()

    def run(self):
        """Runs the main game loop."""
        print("Starting game loop...")
        while self.running:
            print("Ticking clock...")
            dt = self.clock.tick(constants.FPS)
            print(f"dt: {dt}")
            print("Handling events...")
            self.handle_events()
            print("Updating state...")
            self.update(dt)
            print("Rendering...")
            self.render()
        print("Shutting down...")
        self.shutdown()

    def shutdown(self):
        """Shuts down pygame."""
        pygame.quit()

    def export_data(self):
        """
        Exports game state data (player, entities, etc.) as a JSON string.
        This is a placeholder for future implementation.
        """
        llm_char_data = {}
        llm_char = self.state_manager.get_game_state().entities.get(
            self.llm_character_id
        )
        if llm_char:
            llm_char_data = {
                "id": llm_char.id,
                "name": llm_char.name,
                "x": llm_char.x,
                "y": llm_char.y,
                "mood": llm_char.mood,
                "traits": getattr(llm_char, "traits", {}),
            }
        player = self.state_manager.get_game_state().player

        # This second assignment to llm_char_data seems redundant and overwrites the first one.
        # It should be removed or merged with the first one.
        # For now, I will remove it to avoid overwriting the more complete data.
        # if llm_char:
        #     llm_char_data = {
        #         "x": llm_char.x,
        #         "y": llm_char.y,
        #         "name": llm_char.name,
        #         "mood": llm_char.mood,
        #     }

        data = {
            "player": {
                "x": player.x,
                "y": player.y,
                "name": player.name,
            },
            "llm_character": llm_char_data,
            "timeline_log": self.timeline_log,
            "event_log": self.event_log,
            "traits": dict(getattr(llm_char, "traits", {})),  # Add traits at top level
            "timestamp": pygame.time.get_ticks(),  # Using pygame ticks as a simple timestamp
            "version": __version__,
        }

        def default_json_encoder(obj):
            if isinstance(obj, (set, object)) and not isinstance(
                obj, (str, int, float, bool, type(None))
            ):
                return str(obj)
            raise TypeError(
                f"Object of type {obj.__class__.__name__} is not JSON serializable"
            )

        return json.dumps(data, indent=2, default=default_json_encoder)

    def generate_sprite(self, seed: str) -> list[str]:
        """
        Generates a simple procedural sprite based on a seed.
        This is a placeholder implementation.
        """
        if not seed:
            return ["....", ".##.", ".##.", "...."]  # Default fallback sprite

        # Simple example: vary sprite based on seed length
        if len(seed) % 2 == 0:
            return ["XXXX", "X..X", "X..X", "XXXX"]
        return ["O.O", ".O.", "O.O"]

    def export_lore(self) -> str:
        """
        Exports game lore as a JSON string.
        This is a placeholder implementation.
        """
        lore_data = {
            "arc": "The journey of the lone traveler.",
            "glyphs": ["ancient rune", "mystic symbol"],
            "lineage": "Descendants of the first star-gazers.",
        }
        return json.dumps(lore_data, indent=2)

    def generate_overlay(self, mood: str) -> list[str]:
        """
        Generates a simple overlay based on mood.
        This is a placeholder implementation.
        """
        if mood == "happy":
            return ["\\o/", "| |", "/ \\"]
        if mood == "angry":
            return ["X X", "---", "/_\\"]
        return ["...", ". .", "..."]

    def update_planetary_mood(self, mood: str):
        """
        Update the planetary mood based on a string descriptor.
        Maps moods to float values between -1.0 and +1.0.
        Positive values encourage trait growth, negative values hinder it.
        """
        print(f"[update_planetary_mood] Input mood: {mood}")
        mood_map = {
            "serene": 0.5,
            "joyful": 0.7,
            "neutral": 0.0,
            "storm": -0.5,
            "chaotic": -0.7,
            "anxious": -0.3,
            "calm": 0.2,
        }

        # Default to neutral if mood not recognized
        self.planetary_mood = mood_map.get(mood.lower(), 0.0)
        print(f"[update_planetary_mood] Planetary mood set to: {self.planetary_mood}")

        if self.llm_character_id:
            llm_char_in_state = self.state_manager.get_game_state().entities.get(
                self.llm_character_id
            )
            if llm_char_in_state:
                print(
                    f"[update_planetary_mood] Before llm_char_in_state.mood update: {llm_char_in_state.mood}"
                )
                llm_char_in_state.mood = mood if mood.lower() in mood_map else "neutral"
                print(
                    f"[update_planetary_mood] After llm_char_in_state.mood update: {llm_char_in_state.mood}"
                )

    def apply_planetary_event(self, event: str):
        """
        Apply a planetary event that influences both planetary mood and character traits.
        Events map to mood shifts and trait adjustments.
        """
        event = event.lower()
        llm_char = (
            self.state_manager.get_game_state().entities.get(self.llm_character_id)
            if self.llm_character_id
            else None
        )
        print(
            f"[apply_planetary_event] Before event, llm_char.mood: {llm_char.mood if llm_char else 'N/A'}"
        )
        mood_to_set = "neutral"
        if event == "storm":
            mood_to_set = "anxious"
            if llm_char:
                llm_char.traits["courage"] = llm_char.traits.get("courage", 0) - 1
        elif event == "eclipse":
            mood_to_set = "calm"
            if llm_char:
                llm_char.traits["focus"] = llm_char.traits.get("focus", 0) + 1
        elif event == "festival":
            mood_to_set = "joyful"
            if llm_char:
                llm_char.traits["empathy"] = llm_char.traits.get("empathy", 0) + 1

        print(
            f"[apply_planetary_event] Calling update_planetary_mood with: {mood_to_set}"
        )
        self.update_planetary_mood(mood_to_set)
        print(
            f"[apply_planetary_event] After update_planetary_mood, llm_char.mood: {llm_char.mood if llm_char else 'N/A'}"
        )

        # Re-retrieve llm_char to get updated mood
        llm_char = (
            self.state_manager.get_game_state().entities.get(self.llm_character_id)
            if self.llm_character_id
            else None
        )

        # Append to event log
        entry = {
            "timestamp": time.time(),
            "event": event,
            "mood": llm_char.mood,  # Use updated mood
            "traits": dict(llm_char.traits),  # copy
        }
        self.event_log.append(entry)

    def export_timeline(self) -> str:
        """
        Export the accumulated timeline of planetary moods and trait snapshots.
        Returns a JSON string containing the full timeline_log.
        """
        return json.dumps(self.timeline_log, indent=2)

    def export_trait_chart(self) -> str:
        """
        Export current trait values and optionally aggregate history.
        Returns a JSON string with current traits and summary stats.
        """
        llm_char = self.state_manager.get_game_state().entities.get(
            self.llm_character_id
        )
        traits = llm_char.traits if llm_char else {}
        chart = {
            "traits": traits,
            "timestamp": (
                self.timeline_log[-1]["timestamp"] if self.timeline_log else None
            ),
            "history_length": len(self.timeline_log),
        }
        return json.dumps(chart, indent=2)

    def export_constellation(self) -> str:
        """
        Export a constellation view of events, glyphs, and lineage.
        Uses event_log for events, derives glyphs from moods, and includes lineage info.
        """
        # Derive glyphs from moods/events (simple mapping for now)
        glyph_map = {
            "serene": "✦",
            "joyful": "☀",
            "calm": "☽",
            "anxious": "⚡",
            "storm": "☁",
            "chaotic": "☄",
        }
        glyphs = []
        for entry in self.event_log:
            mood = entry.get("mood", "neutral")
            glyphs.append(glyph_map.get(mood, "·"))

        constellation = {
            "events": self.event_log,
            "glyphs": glyphs,
            "lineage": f"Version {getattr(self, '__version__', '0.0.0')}",
        }
        return json.dumps(constellation, indent=2)

    def save_timeline(self, filepath: str):
        """Write timeline_log to disk as JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.export_timeline())

    def save_events(self, filepath: str):
        """Write event_log to disk as JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.export_events())

    def export_events(self) -> str:
        """
        Export the accumulated event log.
        Returns a JSON string containing the full event_log.
        """
        return json.dumps(self.event_log, indent=2)

    def save_constellation(self, filepath: str):
        """Write constellation export to disk as JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.export_constellation())

    def export_coverage_badge(self, coverage_percent: int) -> str:
        """
        Generate a coverage badge in Markdown format and return JSON metadata.
        coverage_percent: integer (0–100)
        """
        badge = CoverageBadge(coverage_percent)
        return badge.to_json_str()

    def export_covenant_badge(self, contributing_ok: bool, conduct_ok: bool) -> str:
        """
        Generate a covenant badge showing whether CONTRIBUTING.md and
        CODE_OF_CONDUCT.md are valid.
        """
        badge = CovenantBadge(contributing_ok, conduct_ok)
        return badge.to_json_str()

    def export_lineage_badge(self) -> str:
        """
        Generate a lineage badge showing the number of timeline entries (ancestral depth).
        """
        depth = len(getattr(self, "timeline_log", []))
        badge = LineageBadge(depth)
        return badge.to_json_str()

    def run_dashboard(self, refresh_interval: float = 2.0):
        """
        Run a simple terminal dashboard that displays current mood, traits, lineage, and badges.
        Refreshes every few seconds until interrupted.
        """
        try:
            while True:
                if os.name == "nt":
                    subprocess.run(["cls"], shell=True, check=True)
                else:
                    subprocess.run(["clear"], check=True)
                content = render_dashboard_content(self)
                print(content)

                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\nDashboard closed.")


def main():
    """The main entry point for the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
