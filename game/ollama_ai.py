"""
ollama_ai.py

Provides a client to interact with a local Ollama model to generate
AI character moves and dialogue for the game.
"""

import requests

OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama2:latest"  # Use the model you have installed


class OllamaClient:
    """A client for interacting with the Ollama API."""

    def __init__(self, api_url=OLLAMA_API_URL, model=MODEL_NAME):
        """
        Initializes the Ollama client.

        Args:
            api_url (str): The URL of the Ollama API.
            model (str): The name of the model to use.
        """
        self.api_url = api_url
        self.model = model

    def _build_prompt(self, player_x, player_y, llm_x, llm_y, game_map):
        """Builds the prompt for the LLM based on the game state."""
        map_str = "\n".join(game_map)
        return f"""
        You are a character in a simple 2D grid-based game.
        Your goal is to move around and interact with the player.
        The map is represented by a grid of characters:
        'G' is grass (walkable)
        'W' is water (not walkable)

        Your current position is ({llm_x}, {llm_y}).
        The player's position is ({player_x}, {player_y}).

        The map is:
        {map_str}

        You can move one step at a time. Your available moves are: up, down, left, right, stay.
        You can also say something short (less than 10 words).

        Based on the player's position and the map, what is your next move and what do you say?
        Your response must be in the format: MOVE: [your move] | SAY: [your dialogue]
        Example: MOVE: up | SAY: Hello there!
        Choose only one move from the available options.
        """

    def _parse_response(self, response_text):
        """Parses the LLM's response to extract the move and dialogue."""
        move = "stay"
        dialogue = "..."

        # Normalize case for parsing keywords
        response_upper = response_text.upper()

        # Find positions of keywords
        move_pos = response_upper.find("MOVE:")
        say_pos = response_upper.find("SAY:")

        # Isolate the move part
        if move_pos != -1:
            # Find the end of the move part (either start of say or end of string)
            end_pos = say_pos if (say_pos > move_pos) else len(response_text)
            move_part = response_text[move_pos + 5:end_pos].strip(" |")
            parsed_move = move_part.strip().lower()
            if parsed_move in ["up", "down", "left", "right", "stay"]:
                move = parsed_move

        # Isolate the say part
        if say_pos != -1:
            # Find the end of the say part (either start of move or end of string)
            end_pos = move_pos if (move_pos > say_pos) else len(response_text)
            dialogue_part = response_text[say_pos + 4:end_pos].strip(" |")
            dialogue = dialogue_part.strip()
            if not dialogue: # handle empty SAY:
                dialogue = "..."

        return move, dialogue

    def get_move(self, player_x, player_y, llm_x, llm_y, game_map):
        """
        Gets the next move and dialogue from the LLM.

        Returns:
            tuple: (str, str) - The chosen move and a line of dialogue.
        """
        prompt = self._build_prompt(player_x, player_y, llm_x, llm_y, game_map)
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=15)
            response.raise_for_status()
            response_text = (
                response.json().get("message", {}).get("content", "").strip()
            )
            return self._parse_response(response_text)

        except requests.exceptions.RequestException as e:
            print(f"LLM Error: Could not connect to Ollama API: {e}")
            return "stay", "I feel disconnected..."


def get_llm_move(player_x, player_y, llm_x, llm_y, game_map):
    """
    Gets the next move and a line of dialogue for the LLM character.

    This is a convenience wrapper around the OllamaClient.

    Returns:
        tuple: (str, str) - The chosen move and a line of dialogue.
    """
    client = OllamaClient()
    return client.get_move(player_x, player_y, llm_x, llm_y, game_map)
