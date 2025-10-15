"""
main.py

Entry point for the game. Handles initialization, event loop, rendering, and
integration with pixel art rendering and dialogue systems.
"""

import pygame
from ollama_ai import get_llm_move

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

    def __init__(self, x, y, art):
        self.x = x  # World coordinates (tile-based)
        self.y = y
        self.art = art

    @property
    def rect(self):
        """Get the entity's position and size as a pygame.Rect."""
        return pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)


def render_pixel_art(surface, pixel_art_lines, rect):
    """
    Render pixel art onto a given surface.

    Args:
        surface (pygame.Surface): The surface to draw on.
        pixel_art_lines (list[str]): ASCII-like lines representing the art.
        rect (pygame.Rect): The rectangle area where the art should be drawn.
    """
    art_height = len(pixel_art_lines)
    art_width = len(pixel_art_lines[0])

    for row_idx, line in enumerate(pixel_art_lines):
        for col_idx, char in enumerate(line):
            color = COLOR_MAP.get(char, BLACK)
            if color != TRANSPARENT:
                # Calculate pixel boundaries without cumulative rounding errors
                start_x = rect.left + (col_idx * rect.width) // art_width
                end_x = rect.left + ((col_idx + 1) * rect.width) // art_width
                start_y = rect.top + (row_idx * rect.height) // art_height
                end_y = rect.top + ((row_idx + 1) * rect.height) // art_height

                pixel_rect = pygame.Rect(
                    start_x, start_y, end_x - start_x, end_y - start_y
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


class Game:
    """Core class to manage game state, logic, and rendering."""

    def __init__(self):
        """Initializes the game, screen, entities, and timers."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("RuneScape-like Pixel Game")
        self.clock = pygame.time.Clock()
        self.running = True

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
        self.player = Entity(20, 15, player_art)

        llm_art = [
            "..RRR...",
            ".RRRRR..",
            ".RR.RR..",
            "..RRR...",
            "..R.R...",
            ".R...R..",
            "RR...RR.",
            "........",
        ]
        self.llm_character = Entity(22, 15, llm_art)

        self.llm_dialogue = "..."
        self.llm_dialogue_timer = 0
        self.dialogue_duration = 4000  # in milliseconds

        self.llm_move_timer = 0
        self.llm_move_interval = 2000  # in milliseconds

        self.camera_offset_x = 0
        self.camera_offset_y = 0

    def handle_events(self):
        """Handles all user input and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                new_x, new_y = self.player.x, self.player.y
                if event.key == pygame.K_UP:
                    new_y -= 1
                elif event.key == pygame.K_DOWN:
                    new_y += 1
                elif event.key == pygame.K_LEFT:
                    new_x -= 1
                elif event.key == pygame.K_RIGHT:
                    new_x += 1

                if (
                    0 <= new_y < len(GAME_MAP)
                    and 0 <= new_x < len(GAME_MAP[0])
                    and GAME_MAP[new_y][new_x] != "W"
                ):
                    self.player.x, self.player.y = new_x, new_y

    def update(self, dt):
        """Updates the state of game objects."""
        self.llm_move_timer += dt
        self.llm_dialogue_timer += dt

        if self.llm_move_timer >= self.llm_move_interval:
            self.llm_move_timer = 0
            move, dialogue = get_llm_move(
                self.player.x,
                self.player.y,
                self.llm_character.x,
                self.llm_character.y,
                GAME_MAP,
            )
            self.llm_dialogue = dialogue
            self.llm_dialogue_timer = 0

            new_llm_x, new_llm_y = self.llm_character.x, self.llm_character.y
            if move == "up":
                new_llm_y -= 1
            elif move == "down":
                new_llm_y += 1
            elif move == "left":
                new_llm_x -= 1
            elif move == "right":
                new_llm_x += 1

            if (
                0 <= new_llm_y < len(GAME_MAP)
                and 0 <= new_llm_x < len(GAME_MAP[0])
                and GAME_MAP[new_llm_y][new_llm_x] != "W"
            ):
                self.llm_character.x, self.llm_character.y = new_llm_x, new_llm_y

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

        # Draw the player
        player_screen_x = self.player.x * TILE_SIZE + self.camera_offset_x
        player_screen_y = self.player.y * TILE_SIZE + self.camera_offset_y
        render_pixel_art(
            self.screen,
            self.player.art,
            pygame.Rect(player_screen_x, player_screen_y, TILE_SIZE, TILE_SIZE),
        )

        # Draw the LLM character
        llm_screen_x = self.llm_character.x * TILE_SIZE + self.camera_offset_x
        llm_screen_y = self.llm_character.y * TILE_SIZE + self.camera_offset_y
        render_pixel_art(
            self.screen,
            self.llm_character.art,
            pygame.Rect(llm_screen_x, llm_screen_y, TILE_SIZE, TILE_SIZE),
        )

        if self.llm_dialogue_timer < self.dialogue_duration:
            draw_text(
                self.screen,
                self.llm_dialogue,
                18,
                pygame.Rect(llm_screen_x, llm_screen_y, TILE_SIZE, TILE_SIZE),
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


def main():
    """The main entry point for the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
