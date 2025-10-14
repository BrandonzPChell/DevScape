"""
ollama_ai.py

Provides a client to interact with a local Ollama model to generate
AI character moves and dialogue for the game.
"""

import heapq
import json
import logging
import re

import requests

_STREAM_CONTENT_RE = re.compile(r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', re.IGNORECASE)

# permissive regex to capture MOVE and a single word direction
_MOVE_DIR_RE = re.compile(r"\bMOVE\b\s*[:\-]?\s*([a-z]+)", re.IGNORECASE)

_SAY_RE = re.compile(
    r'\b(?:SAY|SPEAK)\b\s*[:\-]?\s*("?) (.+?)\1(?:\s*$|\s*\|)', re.IGNORECASE
)

DIRECTION_MAP = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
    "stay": (0, 0),
}


def _find_path_a_star(start, end, game_map):
    """
    Finds a path from start to end using the A* algorithm.
    start, end: (x, y) tuples
    game_map: list of strings representing the map
    Returns: list of (x, y) tuples representing the path, or None if no path found.
    """
    rows = len(game_map)
    cols = len(game_map[0])

    # Helper to check if a position is valid and not a water tile
    def is_valid(x, y):
        return 0 <= y < rows and 0 <= x < cols and game_map[y][x] != "W"

    # Heuristic function (Manhattan distance)
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    open_set = []
    heapq.heappush(open_set, (0, start))  # (f_score, (x, y))

    came_from = {}
    g_score = {(x, y): float("inf") for y in range(rows) for x in range(cols)}
    g_score[start] = 0
    f_score = {(x, y): float("inf") for y in range(rows) for x in range(cols)}
    f_score[start] = heuristic(start, end)

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]  # Reverse to get path from start to end

        x, y = current
        # Neighbors (right, left, down, up)
        neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

        for neighbor in neighbors:
            nx, ny = neighbor
            if is_valid(nx, ny):
                tentative_g_score = (
                    g_score[current] + 1
                )  # Cost of moving to neighbor is 1

                if tentative_g_score < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + heuristic(neighbor, end)
                    if (f_score[neighbor], neighbor) not in open_set:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return None  # No path found


def _direction_to_delta(direction: str) -> tuple[int, int]:
    if direction == "up":
        return (0, -1)
    if direction == "down":
        return (0, 1)
    if direction == "left":
        return (-1, 0)
    if direction == "right":
        return (1, 0)
    return (0, 0)  # "stay" or invalid


MOVE_COORD_REGEX = re.compile(
    r"MOVE\s*:?\s*\[?\s*([+-]?\d+)\s*,\s*([+-]?\d+)\s*\]?", re.IGNORECASE
)
MOVE_DIR_REGEX = re.compile(
    r"MOVE\s*[:]?\s*(?P<direction>up|down|left|right|stay|north|south|east|west)",
    re.IGNORECASE,
)
SAY_REGEX = re.compile(r"SAY:\s*(.+)$", re.IGNORECASE)


def _safe_unescape(raw: str) -> str:
    # First, convert common literal escape sequences so they become actual characters
    # Handles literal backslash-n, backslash-r, backslash-t, escaped quotes and backslash
    raw = raw.replace(r"\\n", "\n")
    raw = raw.replace(r"\\r", "\r")
    raw = raw.replace(r"\\t", "\t")
    raw = raw.replace(r'\\"', '"')
    raw = raw.replace(r"\\'", "'")
    raw = raw.replace(r"\\\\", "\\")

    # Then attempt to decode any remaining escape sequences (unicode_escape is safe here)
    try:
        raw = raw.encode("utf-8").decode("unicode_escape")
    except UnicodeError:
        pass

    return raw


def _parse_line_for_content(line: str) -> list[str]:
    """Parses a single line for content, trying JSON parsing first, then regex."""
    contents = []
    line = line.strip()
    if not line:
        return contents

    # Try to parse a JSON object on this line
    try:
        obj = json.loads(line)
        # nested structure: {"message":{"role":"assistant","content":"..."}}
        # handle both top-level "message" and top-level "content"
        if isinstance(obj, dict):
            # navigate common shapes
            msg = obj.get("message") or obj.get("data") or obj
            if isinstance(msg, dict):
                c = msg.get("content") or msg.get("text")
                if isinstance(c, str):
                    contents.append(c)
                    return contents  # Return early if content found

            # If not found in nested, try top-level content
            c = obj.get("content")
            if isinstance(c, str):
                contents.append(c)
                return contents  # Return early if content found
    except json.JSONDecodeError:
        # not valid JSON line; proceed to regex fallback
        pass

    # Regex fallback on the single line (handles escaped quotes)
    for m in _STREAM_CONTENT_RE.finditer(line):
        # group(1) is an escaped content string; unescape common escapes
        raw_content = m.group(1)
        unescaped = _safe_unescape(raw_content)
        contents.append(unescaped)

    return contents


def _try_parse_raw_json(raw: str) -> str | None:
    """Tries to parse the entire raw string as a single JSON object."""
    try:
        logging.debug("Attempting to parse raw string as JSON: %s", raw)
        obj = json.loads(raw)
        logging.debug("Parsed JSON object: %s", obj)
        if isinstance(obj, dict):
            msg = obj.get("message") or obj.get("data") or obj
            logging.debug("Extracted message/data object: %s", msg)
            if isinstance(msg, dict):
                c = msg.get("content") or msg.get("text")
                logging.debug("Extracted content 'c': %s", c)
                if isinstance(c, str):
                    # If we successfully parse the entire raw string as JSON and find content, return it directly
                    c = c.replace("\xa0", " ").strip()
                    c = " ".join(c.split())
                    return c
            c = obj.get("content")
            if isinstance(c, str):
                logging.debug("Extracted top-level content 'c': %s", c)
                c = c.replace("\xa0", " ").strip()
                c = " ".join(c.split())
                return c
    except json.JSONDecodeError as e:
        logging.debug("JSON parsing failed: %s", e)
    return None


def _extract_stream_contents(raw: str) -> str:
    """
    Accepts raw response text that may be:
      - actual JSON lines per message
      - an escaped/quoted blob with backslashes and \n separators
      - a mix of the above
    Returns joined assistant content string.
    """
    if not raw:
        return ""

    content = _try_parse_raw_json(raw)
    if content is not None:
        return content

    contents = []
    for line in raw.splitlines():
        contents.extend(_parse_line_for_content(line))

    # As an extra fallback, run regex over entire raw text if still empty
    if not contents:
        for m in _STREAM_CONTENT_RE.finditer(raw):
            unescaped = _safe_unescape(m.group(1))
            contents.append(unescaped)

    joined = "".join(contents)
    joined = joined.replace(
        "\xa0", " "
    )  # Replace non-breaking space character with regular space
    joined = re.sub(
        r"[ \t\f\v]+\s*", " ", joined
    )  # Collapse multiple spaces/tabs/etc. (excluding newlines)
    joined = joined.strip()  # Strip leading/trailing whitespace
    return joined


def parse_move_and_dialogue(raw: str):
    full = _extract_stream_contents(raw)  # Use _extract_stream_contents here
    move_part = full if "MOVE" in full.upper() and "|" not in full else None
    if not move_part:
        parts = re.split(r"\s*\|\s*", full) if "|" in full else [full]
        for p in parts:
            if re.search(r"\bMOVE\b", p, re.IGNORECASE):
                move_part = p
                break
    if not move_part:
        move_part = full
    m = _MOVE_DIR_RE.search(move_part or "")  # Use _MOVE_DIR_RE here
    dx, dy = (0, 0)
    if m:
        dir_word = m.group(1).lower()
        dx, dy = DIRECTION_MAP.get(dir_word, (0, 0))
    # dialogue extraction
    say_m = re.search(r"\b(?:SAY|SPEAK)\b\s*[:\-]?\s*(.+)", full, re.IGNORECASE)
    dialogue = ""
    if say_m:
        dialogue = say_m.group(1).strip().strip('"').strip("'")
    return {"move": {"dx": dx, "dy": dy}, "dialogue": dialogue}


def _parse_content_to_move_and_dialogue(full: str | None):
    if full is None:
        full = ""
    """
    Parse a command string and return {"move": {"dx": dx, "dy": dy}, "dialogue": dialogue}.
    Keeps behavior consistent with the parser used in tests.
    """
    # direction extraction (keep your DIRECTION_MAP lookup here)
    move_result = None
    # Try to find coordinate-based move first
    coord_m = MOVE_COORD_REGEX.search(full)
    if coord_m:
        dx = int(coord_m.group(1))
        dy = int(coord_m.group(2))
        move_result = {"dx": dx, "dy": dy}
    else:
        # If no coordinate move, try direction word
        dir_m = MOVE_DIR_REGEX.search(full)
        if dir_m:
            dir_word = dir_m.group("direction").lower()
            dx, dy = DIRECTION_MAP.get(dir_word, (0, 0))
            move_result = {"dx": dx, "dy": dy}

    # dialogue extraction
    say_m = re.search(r"\b(?:SAY|SPEAK)\b\s*[:\-]?\s*(.+)", full, re.IGNORECASE)
    dialogue = ""
    if say_m:
        dialogue = say_m.group(1).strip().strip('"').strip("'")
    elif move_result is None:
        dialogue = full.strip()

    return {"move": move_result, "dialogue": dialogue}


OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama2:latest"  # Use the model you have installed


class OllamaClient:
    """
    A client for interacting with the Ollama API, maintaining conversation history.
    """

    def __init__(self, api_url=OLLAMA_API_URL, model=MODEL_NAME):
        """
        Initializes the Ollama client.

        Args:
            api_url (str): The URL of the Ollama API.
            model (str): The name of the model to use.
        """
        self.api_url = api_url
        self.model = model
        self.message_history = []  # Stores conversation context

        # Initial system message to set the AI's persona
        self.message_history.append(
            {
                "role": "system",
                "content": (
                    "You are a character in a simple 2D grid-based game. "
                    "Your goal is to move around and interact with the player. "
                    "You can also engage in conversation. "
                    "Keep your responses concise and in character."
                ),
            }
        )

    def _send_request(self, messages):
        """
        Send messages to the Ollama API and return a normalized response dict:
        {
            "move": None or parsed move payload,
            "dialogue": string extracted from the LLM content (or empty string),
            "raw": raw response text
        }
        """
        try:
            response = requests.post(
                self.api_url,
                json={"messages": messages, "model": self.model},
                timeout=30,  # Increased timeout
            )

            if response.status_code == 200:
                raw = response.text.strip()
                content = _extract_stream_contents(raw)
                if not content:
                    return {"move": None, "dialogue": raw, "raw": raw}
                parsed = _parse_content_to_move_and_dialogue(content)
                return {
                    "move": parsed.get("move"),
                    "dialogue": parsed.get("dialogue", ""),
                    "raw": content,  # Use extracted content for 'raw' when successful
                }
            logging.error(
                "LLM move request failed with status %s: %s",
                response.status_code,
                response.text,
            )
            return {
                "move": {"dx": 0, "dy": 0},
                "dialogue": f"Error: LLM request failed with status {response.status_code}.",
                "raw": "",
            }
        except requests.exceptions.RequestException as e:
            logging.error(
                "LLM Error: Could not connect to Ollama API: %s", e, exc_info=True
            )
            # Structured fallback for network/request failures
            return {"move": None, "dialogue": "I feel disconnected...", "raw": ""}

    def get_move_and_dialogue(
        self, player_x, player_y, llm_x, llm_y, game_map, llm_mood="neutral"
    ):
        """
        Gets the next move and a line of dialogue for the LLM character,
        considering game state, conversation history, and current mood.

        Returns:
            tuple: (str, str) - The chosen move and a line of dialogue.
        """
        map_str = "\n".join(game_map)

        # Pathfinding to player
        path = _find_path_a_star((llm_x, llm_y), (player_x, player_y), game_map)
        next_step_info = ""
        if path and len(path) > 1:
            next_step = path[1]  # The next tile to move to
            dx = next_step[0] - llm_x
            dy = next_step[1] - llm_y
            if dx == 1:
                next_move_direction = "right"
            elif dx == -1:
                next_move_direction = "left"
            elif dy == 1:
                next_move_direction = "down"
            elif dy == -1:
                next_move_direction = "up"
            else:
                next_move_direction = "stay"
            next_step_info = (
                f"A path to the player exists. "
                f"The next optimal step is to move {next_move_direction}.\n"
            )
        elif path and len(path) == 1:
            next_step_info = "You are at the player's location.\n"
        else:
            next_step_info = "No direct path to the player is currently available.\n"

        move_prompt = (
            f"Current game state:\n"
            f"Map:\n"
            f"{map_str}\n"
            f"Your position: ({llm_x}, {llm_y})\n"
            f"Player position: ({player_x}, {player_y})\n"
            f"Your current mood is: {llm_mood}.\n"
            f"{next_step_info}\n"
            f"You can move one step at a time. Your available moves are: "
            f"up, down, left, right, stay.\n"
            f"You can also say something short (less than 10 words) "
            f"that reflects your current mood.\n\n"
            f"Based on the game state, your mood, and our conversation so far, "
            f"what is your next move and what do you say?\n"
            f"Your response must be in the format: "
            f"MOVE: [your move] | SAY: [your dialogue]\n"
            f"Choose only one move from the available options."
        )

        # Add the move prompt to history for context, but don't store it permanently
        # as a user message, it's a system instruction for this turn.
        temp_messages = self.message_history + [
            {"role": "user", "content": move_prompt}
        ]

        full_response_dict = self._send_request(temp_messages)

        # Extract move and dialogue from the parsed dictionary
        parsed_move = full_response_dict.get("move")
        dialogue = full_response_dict.get("dialogue", "...")

        move_delta = (0, 0)
        if parsed_move:
            move_delta = (parsed_move["dx"], parsed_move["dy"])

        # Add AI's response to history (using the raw content for history)
        self.message_history.append(
            {"role": "assistant", "content": full_response_dict.get("raw", "")}
        )

        return move_delta, dialogue

    def send_message(self, user_message):
        """
        Sends a user message to the LLM and returns its conversational response.
        Maintains conversation history.
        """
        self.message_history.append({"role": "user", "content": user_message})

        ai_response_content = self._send_request(self.message_history)

        self.message_history.append(
            {"role": "assistant", "content": ai_response_content}
        )

        return ai_response_content


# Global client instance for convenience
ollama_client = OllamaClient()


def get_llm_move(player_x, player_y, llm_x, llm_y, game_map, llm_mood):
    """
    Gets the next move and a line of dialogue for the LLM character.
    This is a convenience wrapper around the OllamaClient.
    """
    return ollama_client.get_move_and_dialogue(
        player_x, player_y, llm_x, llm_y, game_map, llm_mood
    )


def send_player_message_to_llm(user_message):
    """
    Sends a player message to the LLM and returns its conversational response.
    This is a convenience wrapper around the OllamaClient.
    """
    return ollama_client.send_message(user_message)
