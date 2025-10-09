"""
main.py

Entry point for the game. Handles initialization, event loop, rendering, and
integration with pixel art rendering and dialogue systems.
"""

import pygame
import json
import logging
import time
import os

from .ollama_ai import OllamaClient, get_llm_move

__version__ = "0.1.0"

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
TRANSPARENT = (0, 0, 0, 0)
DARK_GREEN = (34, 139, 34)
LIGHT_GREEN = (60, 179, 113)
DARK_BLUE = (0, 0, 139)
LIGHT_BLUE = (135, 206, 250)

COLOR_MAP = {
    "X": BLACK,
    "W": WHITE,
    "R": RED,
    ".": TRANSPARENT,
    " ": TRANSPARENT,
    "G": DARK_GREEN,
    "g": LIGHT_GREEN,
    "B": DARK_BLUE,
    "b": LIGHT_BLUE,
    "S": (255, 224, 189),  # Skin
    "H": (139, 69, 19),  # Hair
    "C": (0, 128, 0),  # Clothes (shirt)
    "P": (0, 0, 128),  # Pants
    "F": (139, 69, 19),  # Feet/Shoes
}

MOOD_GLYPHS = {
    "neutral": [], # No glyph for neutral
    "happy": ["..^.^..", ".(o.o).", ".(   ).", r"..\_/..."], # Simple happy face
    "angry": ["..>.<..", ".(o.o).", ".(---).", r"../\_\.."], # Simple angry face
    "tired": ["..-.-..", ".(o.o).", ".(   ).", r"..\_/..."], # Simple tired face
}

# Tile pixel art
GRASS_TILE_ART = ["GgGg", "gGgG", "GgGg", "gGgG"]
WATER_TILE_ART = ["BbBb", "bBbB", "BbBb", "bBbB"]

TILE_ART_MAP = {
    "G": GRASS_TILE_ART,
    "W": WATER_TILE_ART,
}

GAME_MAP = [
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGWWWWWWWWWWWWWWWWWWGGGGGGGGGGGG",
    "GGGGGGGGWWWWWWWWWWWWWWWWWWWWWWGGGGGGGGGG",
    "GGGGGGGWWWWWWWWWWWWWWWWWWWWWWWWGGGGGGGGG",
    "GGGGGGWWWWWWWWWWWWWWWWWWWWWWWWWWGGGGGGGG",
    "GGGGGGWWWWWWWWWWWWWWWWWWWWWWWWWWGGGGGGGG",
    "GGGGGGWWWWWWWWWWWWWWWWWWWWWWWWWWGGGGGGGG",
    "GGGGGGWWWWWWWWWWWWWWWWWWWWWWWWWWGGGGGGGG",
    "GGGGGGWWWWWWWWWWWWWWWWWWWWWWWWWWGGGGGGGG",
    "GGGGGGWWWWWWWWWWWWWWWWWWWWWWWWWWGGGGGGGG",
    "GGGGGGGGWWWWWWWWWWWWWWWWWWWWWWGGGGGGGGGG",
    "GGGGGGGGGGWWWWWWWWWWWWWWWWWWGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
]


class Entity:
    """Represents any object in the game world, like players or NPCs."""

    def __init__(self, name, x, y, art):
        self.name = name
        self.x = x  # World coordinates (tile-based)
        self.y = y
        self.art = art
        self.mood = "neutral"  # New mood attribute
        self.traits = {} # New traits attribute

        # Chat bubble state
        self.bubble_text = ""
        self.bubble_start_time = 0
        self.bubble_duration = 3000  # ms
        self.bubble_expires = 0

    @property
    def rect(self):
        """Get the entity's position and size as a pygame.Rect."""
        return pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def move(self, dx, dy, game_map):
        """Move the entity by dx, dy tiles, respecting map boundaries and preventing diagonal movement."""
        if dx != 0 and dy != 0:  # Prevent diagonal movement
            return

        new_x, new_y = self.x + dx, self.y + dy
        if (
            0 <= new_y < len(game_map)
            and 0 <= new_x < len(game_map[0])
            and game_map[new_y][new_x] != "W"
        ):
            self.x, self.y = new_x, new_y


def render_pixel_art(surface, pixel_art_lines, rect):
    """
    Render pixel art onto a given surface.

    Args:
        surface (pygame.Surface): The surface to draw on.
        pixel_art_lines (list[str]): ASCII-like lines representing the art.
        rect (pygame.Rect): The rectangle area where the art should be drawn.
    """
    art_height = len(pixel_art_lines)
    if art_height == 0:
        return
    art_width = len(pixel_art_lines[0])
    pixel_w = rect.width / art_width
    pixel_h = rect.height / art_height

    for row_idx, line in enumerate(pixel_art_lines):
        for col_idx, char in enumerate(line):
            color = COLOR_MAP.get(char, BLACK)
            if color != TRANSPARENT:
                pixel_rect = pygame.Rect(
                    rect.left + col_idx * pixel_w,
                    rect.top + row_idx * pixel_h,
                    pixel_w,
                    pixel_h,
                )
                surface.fill(color, pixel_rect)


def draw_text(surface, text, size, rect, color=WHITE):
    """
    Draws text onto a surface, centered above a specified rect.

    Args:
        surface (pygame.Surface): The surface to draw on.
        text (str): The text content to render.
        size (int): The font size.
        rect (pygame.Rect): The rect to position the text relative to.
        color (tuple, optional): The color of the text. Defaults to WHITE.
    """
    font = pygame.font.Font(pygame.font.get_default_font(), size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.center = (rect.centerx, rect.top - 10)
    surface.blit(text_surface, text_rect)


def draw_chat_bubble(surface, text, position, font, duration=3000, start_time=None, bubble_expires_time=None):
    """
    Draw a chat bubble above a character's head.

    Args:
        surface (pygame.Surface): The surface to draw on.
        text (str): The message to display.
        position (tuple): (x, y) coordinates of the character's head.
        font (pygame.font.Font): Font for rendering text.
        duration (int): How long (ms) the bubble should last.
        start_time (int): The tick when the bubble appeared.
        bubble_expires_time (int): The tick when the bubble should expire.
    """
    padding = 6 # Moved padding definition here
    if not text:
        return

    # If timing is tracked, fade out after duration
    if bubble_expires_time is not None:
        now = pygame.time.get_ticks()
        if now >= bubble_expires_time:
            return  # bubble expired

    # Render text
    wrapped_lines = []
    words = text.split(' ')
    current_line = []
    max_bubble_width = SCREEN_WIDTH // 3  # Example max width for bubble

    for word in words:
        test_line = ' '.join(current_line + [word])
        test_width, _ = font.size(test_line)
        if test_width > max_bubble_width and current_line:
            wrapped_lines.append(' '.join(current_line))
            current_line = [word]
        else:
            current_line.append(word)
    wrapped_lines.append(' '.join(current_line))

    text_surfaces = [font.render(line, True, (0, 0, 0)) for line in wrapped_lines]
    
    # Calculate bubble dimensions based on wrapped text
    bubble_width = max(surface.get_width() for surface in text_surfaces) + padding * 2
    bubble_height = sum(surface.get_height() for surface in text_surfaces) + padding * 2

    # Position bubble slightly above the character
    bubble_x = position[0] - bubble_width // 2
    bubble_y = position[1] - bubble_height - 10

    # Draw bubble background (white with black border)
    bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)
    pygame.draw.rect(surface, (255, 255, 255), bubble_rect, border_radius=8)
    pygame.draw.rect(surface, (0, 0, 0), bubble_rect, 2, border_radius=8)

    # Blit text inside bubble
    text_y = bubble_y + padding
    for text_surface in text_surfaces:
        text_x = bubble_x + padding
        surface.blit(text_surface, (text_x, text_y))
        text_y += text_surface.get_height()


def render_dashboard_content(game_instance) -> str:
    """
    Return a string snapshot of the dashboard for the current game state.
    This function is pure: it does not block, print, or wait for input.
    """
    lines = []

    # Header
    lines.append("=== DevScape Dashboard ===")

    # Player info
    if hasattr(game_instance, "player"):
        lines.append(f"Player: {game_instance.player.name} at ({game_instance.player.x}, {game_instance.player.y})")

    # LLM Character info
    if hasattr(game_instance, "llm_character"):
        mood = getattr(game_instance.llm_character, "mood", "unknown")
        traits = getattr(game_instance.llm_character, "traits", {})
        lines.append(f"Mood: {mood}")
        if traits:
            trait_str = ", ".join(f"{k}: {v}" for k, v in traits.items())
            lines.append(f"Traits: {trait_str}")

    # Timeline summary
    if getattr(game_instance, "timeline_log", []):
        lines.append(f"Timeline entries: {len(game_instance.timeline_log)}")

    # Event summary
    if getattr(game_instance, "event_log", []):
        last_event = game_instance.event_log[-1]
        lines.append(f"Last event: {last_event.get('event', 'unknown')}")

    # Footer
    lines.append("==========================")

    return "\n".join(lines)


class Game:
    """Core class to manage game state, logic, and rendering."""

    def __init__(self):
        """Initializes the game, screen, entities, and timers."""
        pygame.init()
        pygame.font.init()  # Initialize font module
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("RuneScape-like Pixel Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)  # Font for chat
        self.running = True

        # Game state
        self.is_typing = False
        self.input_text = ""
        self.in_chat_mode = False  # Are we currently typing a message?
        self.chat_buffer = ""  # The text being composed

        self.map_width_pixels = len(GAME_MAP[0]) * TILE_SIZE
        self.map_height_pixels = len(GAME_MAP) * TILE_SIZE

        player_art = [
            "..HHHH..",
            ".HSSH...",
            ".HSSSH..",
            "..SCS...",
            "..CCC...",
            "..PPP...",
            ".P.P....",
            ".F.F....",
        ]
        self.player = Entity("Player", 20, 15, player_art)

        llm_art = [
            "..RRR...",
            ".RRRRR..",
            ".RR.RR..",
            "..RRR...",
            ".R.R...",
            ".R...R..",
            "RR...RR.",
            "........",
        ]
        self.llm_character = Entity("AI", 22, 15, llm_art)

        self.entities = [self.player, self.llm_character]

        self.ollama_client = OllamaClient()  # Instantiate OllamaClient

        self.llm_move_timer = 0
        self.llm_move_interval = 2000  # in milliseconds

        self.camera_offset_x = 0
        self.camera_offset_y = 0

        self.should_speak = True  # New attribute for conditional speech
        self.planetary_mood = 0.0 # Initialize planetary mood

        self.timeline_log = []       # list of {timestamp, mood, traits}
        self.event_log = []          # list of {timestamp, event, mood, trait_changes}

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
        if self.in_chat_mode:
            if key == pygame.K_RETURN:
                if self.chat_buffer.strip():
                    self.send_player_message(self.chat_buffer)
                self.chat_buffer = ""
                self.in_chat_mode = False
            elif key == pygame.K_ESCAPE:
                self.chat_buffer = ""
                self.in_chat_mode = False
            elif key == pygame.K_BACKSPACE:
                self.chat_buffer = self.chat_buffer[:-1]
            else:
                # Simulate TEXTINPUT for character keys
                char = pygame.key.name(key)
                if len(char) == 1:  # Only add single characters to chat buffer
                    self.chat_buffer += char
        else:
            if key == pygame.K_t:
                self.in_chat_mode = True
                self.chat_buffer = ""
            elif key == pygame.K_UP:
                self.player.move(0, -1, GAME_MAP)
            elif key == pygame.K_DOWN:
                self.player.move(0, 1, GAME_MAP)
            elif key == pygame.K_LEFT:
                self.player.move(-1, 0, GAME_MAP)
            elif key == pygame.K_RIGHT:
                self.player.move(1, 0, GAME_MAP)

    def handle_text_input(self, text):
        """
        Simulates a text input event for testing purposes.
        """
        if self.in_chat_mode:
            self.chat_buffer += text

    def send_player_message(self, message: str):
        """Handles sending a player message to the AI and displaying responses."""
        logging.info(f"Player message sent: '{message}'")
        # Show player’s bubble
        self.show_chat_bubble(self.player, message)

        # Send to AI spirit
        try:
            reply = self.ollama_client.send_message(message)
            logging.info(f"AI replied: '{reply}'")
        except Exception as e:
            logging.error(f"Error during AI interaction: {e}", exc_info=True)
            reply = "I'm having trouble responding right now..."

        # Show AI’s bubble
        self.show_chat_bubble(self.llm_character, reply)

    def handle_events(self):
        """Handles all user input and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if self.in_chat_mode:
                    # Handle chat-specific keys
                    if event.key == pygame.K_RETURN:
                        if self.chat_buffer.strip():
                            self.send_player_message(self.chat_buffer)
                        self.chat_buffer = ""
                        self.in_chat_mode = False
                    elif event.key == pygame.K_ESCAPE:
                        # Cancel chat
                        self.chat_buffer = ""
                        self.in_chat_mode = False
                    elif event.key == pygame.K_BACKSPACE:
                        self.chat_buffer = self.chat_buffer[:-1]
                    # Other keys are handled by TEXTINPUT
                else:
                    # Normal gameplay keys
                    if event.key == pygame.K_t:
                        # Enter chat mode
                        self.in_chat_mode = True
                        self.chat_buffer = ""  # Clear input when entering chat
                    elif event.key == pygame.K_UP:
                        self.player.move(0, -1, GAME_MAP)
                    elif event.key == pygame.K_DOWN:
                        self.player.move(0, 1, GAME_MAP)
                    elif event.key == pygame.K_LEFT:
                        self.player.move(-1, 0, GAME_MAP)
                    elif event.key == pygame.K_RIGHT:
                        self.player.move(1, 0, GAME_MAP)

            elif event.type == pygame.TEXTINPUT and self.in_chat_mode:
                # Collect typed characters into buffer
                self.chat_buffer += event.text

    def update(self, dt: int):
        """Updates the state of game objects, including AI and dialogue."""
        now = pygame.time.get_ticks()

        # Expire chat bubbles
        now = pygame.time.get_ticks()
        for entity in self.entities:
            if entity.bubble_text and entity.bubble_expires <= now:
                entity.bubble_text = ""
                entity.bubble_start_time = 0
                entity.bubble_duration = 0
                entity.bubble_expires = 0

        # Advance timers
        self.llm_move_timer += dt

        # Check for LLM character move
        while self.llm_move_timer >= self.llm_move_interval: # Change if to while
            self.llm_move_timer -= self.llm_move_interval # Subtract the interval, don't reset to 0
            move_delta = (0, 0)
            dialogue = None
            try:
                move_delta, dialogue = get_llm_move(
                    self.player.x,
                    self.player.y,
                    self.llm_character.x,
                    self.llm_character.y,
                    GAME_MAP,
                    self.llm_character.mood,
                )
                logging.debug(f"LLM move: {move_delta}, dialogue: {dialogue}")
            except Exception as e:
                logging.error(f"Error getting LLM move: {e}", exc_info=True)
                # Fallback to no movement and show a silent indicator
                move_delta = (0, 0)
                dialogue = None # Ensure no dialogue is shown on error

            if move_delta == (0, 0) and not self.should_speak: # "none" is now (0,0)
                mood = getattr(self.llm_character, "mood", "neutral")
                indicators = {
                    "neutral": "...",
                    "tired": "zzz",
                    "angry": "—",
                    "happy": "♪",
                }
                indicator = indicators.get(mood, "...")
                print(f"Calling show_chat_bubble for silent indicator with mood: {mood}") # Debug print
                self.show_chat_bubble(self.llm_character, indicator, duration=1000)
            else:
                # Apply movement logic
                dx, dy = move_delta
                new_llm_x, new_llm_y = self.llm_character.x + dx, self.llm_character.y + dy

                if (
                    0 <= new_llm_y < len(GAME_MAP)
                    and 0 <= new_llm_x < len(GAME_MAP[0])
                    and GAME_MAP[new_llm_y][new_llm_x] != "W"
                ):
                    self.llm_character.x, self.llm_character.y = new_llm_x, new_llm_y

                if (
                    self.should_speak and dialogue
                ):  # Only show bubble if there is dialogue and should_speak is True
                    self.show_chat_bubble(self.llm_character, dialogue)

        # Update camera to center on player
        self.camera_offset_x = SCREEN_WIDTH // 2 - self.player.x * TILE_SIZE
        self.camera_offset_y = SCREEN_HEIGHT // 2 - self.player.y * TILE_SIZE

        # Clamp camera to map boundaries
        self.camera_offset_x = min(self.camera_offset_x, 0)
        self.camera_offset_y = min(self.camera_offset_y, 0)
        self.camera_offset_x = max(
            self.camera_offset_x, SCREEN_WIDTH - self.map_width_pixels
        )
        self.camera_offset_y = max(
            self.camera_offset_y, SCREEN_HEIGHT - self.map_height_pixels
        )

        # Trait evolution
        if hasattr(self.llm_character, "traits"):
            # Ensure planetary_mood exists; default to neutral (0.0)
            mood_value = getattr(self, "planetary_mood", 0.0)
            mood_factor = max(0.0, 1.0 + mood_value)  # clamp to [0, 2]

            base_evolution_rate = 0.1  # per second

            for trait_name, current_value in self.llm_character.traits.items():
                if trait_name == "patience":  # evolve patience for now
                    change = base_evolution_rate * dt * mood_factor
                    self.llm_character.traits[trait_name] = current_value + change

        # Append to timeline log (throttle if needed)
        snapshot = {
            "timestamp": time.time(),
            "mood": getattr(self.llm_character, "mood", "neutral"),
            "traits": dict(getattr(self.llm_character, "traits", {})),  # copy
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
                    tile_screen_x = col_idx * TILE_SIZE + self.camera_offset_x
                    tile_screen_y = row_idx * TILE_SIZE + self.camera_offset_y
                    # Cull tiles that are off-screen
                    if (
                        -TILE_SIZE < tile_screen_x < SCREEN_WIDTH
                        and -TILE_SIZE < tile_screen_y < SCREEN_HEIGHT
                    ):
                        render_pixel_art(
                            self.screen,
                            tile_art,
                            pygame.Rect(
                                tile_screen_x, tile_screen_y, TILE_SIZE, TILE_SIZE
                            ),
                        )

        # Draw entities and their chat bubbles
        for entity in self.entities:
            entity_screen_x = entity.x * TILE_SIZE + self.camera_offset_x
            entity_screen_y = entity.y * TILE_SIZE + self.camera_offset_y
            render_pixel_art(
                self.screen,
                entity.art,
                pygame.Rect(entity_screen_x, entity_screen_y, TILE_SIZE, TILE_SIZE),
            )
            # Draw mood overlay for llm_character
            if entity == self.llm_character and entity.mood in MOOD_GLYPHS and MOOD_GLYPHS[entity.mood]:
                mood_art = MOOD_GLYPHS[entity.mood]
                # Position overlay slightly above and to the right of the character
                overlay_rect = pygame.Rect(
                    entity_screen_x + TILE_SIZE // 2,
                    entity_screen_y - TILE_SIZE // 2,
                    TILE_SIZE // 2,
                    TILE_SIZE // 2,
                )
                render_pixel_art(self.screen, mood_art, overlay_rect)

            # Draw chat bubble if active
            if entity.bubble_text:
                # Position bubble above the entity's head
                bubble_pos_x = entity_screen_x + TILE_SIZE // 2
                bubble_pos_y = entity_screen_y
                draw_chat_bubble(
                    self.screen,
                    entity.bubble_text,
                    (bubble_pos_x, bubble_pos_y),
                    self.font,
                    duration=entity.bubble_duration,
                    start_time=entity.bubble_start_time,
                    bubble_expires_time=entity.bubble_expires,
                )

        # Draw chat input box if typing
        if self.is_typing:
            input_box_rect = pygame.Rect(50, SCREEN_HEIGHT - 50, SCREEN_WIDTH - 100, 40)
            pygame.draw.rect(self.screen, WHITE, input_box_rect, border_radius=5)
            pygame.draw.rect(self.screen, BLACK, input_box_rect, 2, border_radius=5)
            input_text_surface = self.font.render(self.input_text + "|", True, BLACK)
            self.screen.blit(
                input_text_surface, (input_box_rect.x + 5, input_box_rect.y + 10)
            )

        pygame.display.flip()

    def run(self):
        """Runs the main game loop."""
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.render()
        self.shutdown()

    def shutdown(self):
        """Shuts down pygame."""
        pygame.quit()

    def export_data(self):
        """
        Exports game state data (player, entities, etc.) as a JSON string.
        This is a placeholder for future implementation.
        """
        data = {
            "player": {"x": self.player.x, "y": self.player.y, "name": self.player.name},
            "llm_character": {"x": self.llm_character.x, "y": self.llm_character.y, "name": self.llm_character.name, "mood": self.llm_character.mood},
            "timestamp": pygame.time.get_ticks(), # Using pygame ticks as a simple timestamp
            "version": __version__
        }
        return json.dumps(data, indent=2)

    def generate_sprite(self, seed: str) -> list[str]:
        """
        Generates a simple procedural sprite based on a seed.
        This is a placeholder implementation.
        """
        if not seed:
            return ["....", ".##.", ".##.", "...."] # Default fallback sprite
        
        # Simple example: vary sprite based on seed length
        if len(seed) % 2 == 0:
            return ["XXXX", "X..X", "X..X", "XXXX"]
        else:
            return ["O.O", ".O.", "O.O"]

    def export_lore(self) -> str:
        """
        Exports game lore as a JSON string.
        This is a placeholder implementation.
        """
        lore_data = {
            "arc": "The journey of the lone traveler.",
            "glyphs": ["ancient rune", "mystic symbol"],
            "lineage": "Descendants of the first star-gazers."
        }
        return json.dumps(lore_data, indent=2)

    def generate_overlay(self, mood: str) -> list[str]:
        """
        Generates a simple overlay based on mood.
        This is a placeholder implementation.
        """
        if mood == "happy":
            return ["\\o/", "| |", "/ \\"]
        elif mood == "angry":
            return ["X X", "---", "/_\\"]
        else:
            return ["...", ". .", "..."]

    def update_planetary_mood(self, mood: str):
        """
        Update the planetary mood based on a string descriptor.
        Maps moods to float values between -1.0 and +1.0.
        Positive values encourage trait growth, negative values hinder it.
        """
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

        # Optionally sync character mood string for overlays
        if hasattr(self, "llm_character"):
            self.llm_character.mood = mood if mood.lower() in mood_map else "neutral"



    def apply_planetary_event(self, event: str):
        """
        Apply a planetary event that influences both planetary mood and character traits.
        Events map to mood shifts and trait adjustments.
        """
        event = event.lower()
        if event == "storm":
            # Storms make the world anxious and test courage
            self.update_planetary_mood("anxious")
            if hasattr(self.llm_character, "traits"):
                self.llm_character.traits["courage"] = (
                    self.llm_character.traits.get("courage", 0) - 1
                )
        elif event == "eclipse":
            # Eclipses bring calm introspection
            self.update_planetary_mood("calm")
            if hasattr(self.llm_character, "traits"):
                self.llm_character.traits["focus"] = (
                    self.llm_character.traits.get("focus", 0) + 1
                )
        elif event == "festival":
            # Festivals lift spirits and boost empathy
            self.update_planetary_mood("joyful")
            if hasattr(self.llm_character, "traits"):
                self.llm_character.traits["empathy"] = (
                    self.llm_character.traits.get("empathy", 0) + 1
                )
        else:
            # Unknown events default to neutral
            self.update_planetary_mood("neutral")

        # Append to event log
        entry = {
            "timestamp": time.time(),
            "event": event,
            "mood": self.llm_character.mood,
            "traits": dict(self.llm_character.traits), # copy
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
        traits = getattr(self.llm_character, "traits", {})
        chart = {
            "traits": traits,
            "timestamp": self.timeline_log[-1]["timestamp"] if self.timeline_log else None,
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
            f.write(json.dumps(self.event_log, indent=2))

    def save_constellation(self, filepath: str):
        """Write constellation export to disk as JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.export_constellation())

    def export_coverage_badge(self, coverage_percent: int) -> str:
        """
        Generate a coverage badge in Markdown format and return JSON metadata.
        coverage_percent: integer (0–100)
        """
        color = "red"
        if coverage_percent >= 85:
            color = "brightgreen"
        elif coverage_percent >= 70:
            color = "yellow"
        elif coverage_percent >= 50:
            color = "orange"

        badge_md = f"![Coverage](https://img.shields.io/badge/coverage-{coverage_percent}%25-{color})"
        badge_json = {
            "type": "coverage",
            "value": coverage_percent,
            "color": color,
            "markdown": badge_md,
        }
        return json.dumps(badge_json, indent=2)


    def export_covenant_badge(self, contributing_ok: bool, conduct_ok: bool) -> str:
        """
        Generate a covenant badge showing whether CONTRIBUTING.md and CODE_OF_CONDUCT.md are valid.
        """
        status = "passing" if contributing_ok and conduct_ok else "failing"
        color = "brightgreen" if status == "passing" else "red"

        badge_md = f"![Covenants](https://img.shields.io/badge/covenants-{status}-{color})"
        badge_json = {
            "type": "covenants",
            "status": status,
            "color": color,
            "markdown": badge_md,
        }
        return json.dumps(badge_json, indent=2)


    def export_lineage_badge(self) -> str:
        """
        Generate a lineage badge showing the number of timeline entries (ancestral depth).
        """
        depth = len(getattr(self, "timeline_log", []))
        color = "blue" if depth > 0 else "lightgrey"

        badge_md = f"![Lineage](https://img.shields.io/badge/lineage-{depth}_entries-{color})"
        badge_json = {
            "type": "lineage",
            "entries": depth,
            "color": color,
            "markdown": badge_md,
        }
        return json.dumps(badge_json, indent=2)

    def run_dashboard(self, refresh_interval: float = 2.0):
        """
        Run a simple terminal dashboard that displays current mood, traits, lineage, and badges.
        Refreshes every few seconds until interrupted.
        """
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear")
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
