# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32
FPS = 60
NODE_WIDTH = TILE_SIZE
NODE_HEIGHT = TILE_SIZE

# World dimensions
WORLD_DIMENSIONS = (20, 15)  # Width, Height in tiles
MAP_BOUNDARY_X = WORLD_DIMENSIONS[0]
MAP_BOUNDARY_Y = WORLD_DIMENSIONS[1]

# Player initial stats
PLAYER_INITIAL_HEALTH = 100
PLAYER_INITIAL_XP = 0
PLAYER_INITIAL_LEVEL = 1
PLAYER_INITIAL_POSITION = (WORLD_DIMENSIONS[0] // 2, WORLD_DIMENSIONS[1] // 2)
PLAYER_SIGHT_RANGE = 5
ENEMY_SIGHT_RANGE = 3
MAX_INVENTORY_SIZE = 10
MOVEMENT_COST = 1

# Combat
ATTACK_DAMAGE = 10
ATTACK_RANGE = 1
CRITICAL_HIT_CHANCE = 0.1  # 10% chance
CRITICAL_HIT_MULTIPLIER = 1.5

# XP and Leveling
BASE_REWARD = 5
EXPLORATION_REWARD = 2
LEVEL_UP_THRESHOLDS = {
    1: 10,
    2: 25,
    3: 50,
    4: 100,
    5: 200,
}

# Health Potions
HEALTH_POTION_HEAL = 25

# Fog of War
FOG_OF_WAR_RADIUS = 3

# Entity Types
ENTITY_TYPES = {
    "PLAYER": "PLAYER",
    "ENEMY": "ENEMY",
    "NPC": "NPC",
    "RESOURCE": "RESOURCE",
    "ITEM": "ITEM",
    "GENERIC": "GENERIC",
}

# Entity Colors
ENTITY_COLORS = {
    "PLAYER": (0, 255, 0, 255),  # Green
    "ENEMY": (255, 0, 0, 255),  # Red
    "NPC": (0, 0, 255, 255),  # Blue
    "RESOURCE": (255, 165, 0, 255),  # Orange
    "ITEM": (255, 255, 0, 255),  # Yellow
    "GENERIC": (255, 255, 255, 255),  # White
}

# Tile Types and Colors
TILE_TYPES = {
    "GRASS": "GRASS",
    "WATER": "WATER",
    "FOREST": "FOREST",
    "MOUNTAIN": "MOUNTAIN",
    "ROAD": "ROAD",
}

TILE_COLORS = {
    "GRASS": (34, 139, 34, 255),
    "WATER": (0, 0, 139, 255),
    "FOREST": (34, 80, 34, 255),
    "MOUNTAIN": (100, 100, 100, 255),
    "ROAD": (120, 120, 120, 255),
    "WOOD": (139, 69, 19, 255),  # Brown
    "STONE": (169, 169, 169, 255),  # Dark Grey
    "IRON": (105, 105, 105, 255),  # Grey
}

# Item Types and Effects
ITEM_TYPES = {
    "HEALTH_POTION": "HEALTH_POTION",
    "GOLD_COIN": "GOLD_COIN",
    "SWORD": "SWORD",
}

ITEM_EFFECTS = {
    "HEALTH_POTION": {"heal": HEALTH_POTION_HEAL},
    "GOLD_COIN": {"gold": 10},
    "SWORD": {"damage_bonus": 5},
}

# Resource Types
RESOURCE_TYPES = {
    "WOOD": "WOOD",
    "STONE": "STONE",
    "IRON": "IRON",
}

# Quest Types and Rewards
QUEST_TYPES = {
    "SLAY_ENEMY": "SLAY_ENEMY",
    "COLLECT_RESOURCE": "COLLECT_RESOURCE",
    "EXPLORE_AREA": "EXPLORE_AREA",
}

QUEST_REWARDS = {
    "SLAY_ENEMY": {"xp": 20, "gold": 15},
    "COLLECT_RESOURCE": {"xp": 10, "gold": 5},
    "EXPLORE_AREA": {"xp": 15, "gold": 10},
}

# NPC Dialogue
NPC_DIALOGUE = {
    "Elder": "Greetings, traveler. The path ahead is fraught with peril.",
    "Merchant": "Welcome! Care to browse my wares?",
    "Guard": "Halt! Who goes there?",
}

# Event Types and Descriptions
EVENT_TYPES = {
    "HEALING_AURA": "HEALING_AURA",
    "ENEMY_AMBUSH": "ENEMY_AMBUSH",
    "TREASURE_DISCOVERY": "TREASURE_DISCOVERY",
}

EVENT_DESCRIPTIONS = {
    "HEALING_AURA": "A warm aura washes over you, mending your wounds.",
    "ENEMY_AMBUSH": "You are ambushed by a group of enemies!",
    "TREASURE_DISCOVERY": "You stumble upon a hidden treasure chest!",
}

EVENT_EFFECTS = {
    "HEALING_AURA": {"heal": 20},
    "ENEMY_AMBUSH": {"spawn_enemies": 2},
    "TREASURE_DISCOVERY": {"spawn_item": "GOLD_COIN"},
}

GAME_EVENTS = [
    "HEALING_AURA",
    "ENEMY_AMBUSH",
    "TREASURE_DISCOVERY",
]

GAME_OVER_MESSAGES = [
    "Your journey ends here, brave adventurer.",
    "The world fades to black...",
    "You fought valiantly, but fate had other plans.",
]

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
    "X": WHITE,
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
