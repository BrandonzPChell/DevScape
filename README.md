# Pygame Pixel Art Game with AI

This is a simple 2D grid-based game developed using Pygame. It features a player-controlled character and an AI-controlled character that uses a local Large Language Model (LLM) via Ollama to decide its movements and dialogue.

## Features

*   **2D Grid-Based Movement:** Navigate a map made of grass and water tiles.
*   **Pixel Art Graphics:** Simple, retro-style pixel art for the characters and environment.
*   **AI-Powered NPC:** An NPC that uses an LLM to generate its behavior in real-time.
*   **Dynamic Dialogue:** The AI character can generate and display short lines of dialogue.
*   **Camera System:** The camera follows the player and stays within the map boundaries.

## Requirements

*   Python 3.x
*   Pygame
*   Requests
*   Ollama with a running model (e.g., `llama2`)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r game/requirements.txt
    ```

3.  **Set up Ollama:**
    *   Install Ollama from [ollama.ai](https://ollama.ai/).
    *   Pull a model to be used by the game:
        ```bash
        ollama pull llama2
        ```
    *   Ensure the Ollama application is running in the background.

## Usage

To run the game, execute the `main.py` script:

```bash
python game/main.py
```

**Controls:**
*   **Arrow Keys:** Move the player character (Up, Down, Left, Right).

## Testing

The project uses `pytest` for testing. To run the tests, use the following command from the root directory:

```bash
pytest game/test_game.py
```