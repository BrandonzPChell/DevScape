"""
ollama_ai.py

Provides a client to interact with a local Ollama model to generate
AI character moves and dialogue for the game.
"""

import heapq

import requests


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
    elif direction == "down":
        return (0, 1)
    elif direction == "left":
        return (-1, 0)
    elif direction == "right":
        return (1, 0)
    return (0, 0)  # "stay" or invalid


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
        """Helper to send messages to the Ollama API and handle common errors."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        try:
            response = requests.post(
                self.api_url, json=payload, timeout=30
            )  # Increased timeout
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "").strip()
        except requests.exceptions.RequestException as e:
            print(f"LLM Error: Could not connect to Ollama API: {e}")
            return "I feel disconnected..."

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
            next_step_info = f"A path to the player exists. The next optimal step is to move {next_move_direction}.\n"
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
            f"You can also say something short (less than 10 words) that reflects your current mood.\n\n"
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

        full_response = self._send_request(temp_messages)

        move_delta = (0, 0) # Default to stay
        dialogue = "..."
        if "|" in full_response:
            parts = full_response.split("|")
            move_part = parts[0].replace("MOVE:", "").strip().lower()
            dialogue_part = parts[1].replace("SAY:", "").strip()

            move_delta = _direction_to_delta(move_part)
            dialogue = dialogue_part
        else:  # If the LLM doesn't follow format, just use the whole response as dialogue
            dialogue = full_response

        # Add AI's response to history
        self.message_history.append({"role": "assistant", "content": full_response})

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
