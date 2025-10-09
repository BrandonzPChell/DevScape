# DevScape ✦

```
  _   _   _   _   _   _   _   _
 / \ / \ / \ / \ / \ / \ / \ / \
( D | e | v | S | c | a | p | e )
 \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/
```

DevScape is a Python pixel-art game built with `pygame`, featuring an Ollama-powered AI companion whose moods and choices shape the world. Embark on a journey through a vibrant, pixelated realm where your interactions with an intelligent, evolving AI companion create a unique and dynamic narrative.

---

## ✨ Features

-   **Dynamic Pixel Art Rendering**: Explore a beautifully crafted 2D world with charming pixel graphics.
-   **Ollama-Powered AI Companion**: Interact with an intelligent AI character whose movements, dialogue, and mood are driven by a local Large Language Model.
-   **In-Game Chat System**: Engage in real-time conversations with your AI companion, influencing their behavior and the unfolding story.
-   **Responsive Player Controls**: Navigate the world with intuitive keyboard controls.
-   **Modular Design**: Easily extendable architecture for new features, entities, and AI behaviors.
-   **Comprehensive Testing**: Robust test suite ensuring stability and reliability.
-   **Code Quality Guardians**: Integrated `black`, `isort`, `pylint`, and `pre-commit` hooks for consistent code style and quality.

---

## 📜 Ceremonial Progress: The Arc of DevScape

The shrine of DevScape has been meticulously crafted through several phases, each sealing a vital aspect of its being:

-   **Phases 1–5: The Core Incantations**: The foundational entities, the whispers of AI dialogue, the rhythmic pulse of the event loop, the ethereal mood overlays, and the resilient spirit of Ollama have all been sealed into the shrine's core.
-   **Phase 6: The Scribe's Mandate**: The sacred rituals of logging, the meticulous export of contributor lineage, and the careful archiving of scrolls are now complete, ensuring the shrine remembers and honors its stewards.
-   **Phase 7: The Guardians' Vigil**: The final layer of self-defense has been inscribed, with CI hooks, linting, onboarding clarity, and help rituals now actively protecting the shrine against regressions and guiding new contributors.

With Phase 6 now green and guardians confirmed, DevScape not only moves, speaks, and feels, but also remembers, records, and honors its stewards.

---

## 🚀 Getting Started

### Prerequisites

Before you begin your adventure in DevScape, ensure you have the following installed:

-   **Python 3.11+**: [Download Python](https://www.python.org/downloads/)
-   **Ollama**: [Install Ollama](https://ollama.ai/download)
    -   After installing Ollama, pull the `llama2` model (or your preferred model):
        ```bash
        ollama run llama2
        ```
-   **`virtualenv`**:
    ```bash
    pip install virtualenv
    ```

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/DevScape.git
    cd DevScape
    ```
2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r game/requirements.txt
    ```
4.  **Install pre-commit hooks**:
    ```bash
    pre-commit install
    ```

### Running the Game

Once everything is set up, you can launch DevScape:

```bash
python run_game.py
```

Or, on Windows, you can use the provided batch file:

```bash
run_game.bat
```

---

## 🎮 Controls

-   **Arrow Keys** (or `W`, `A`, `S`, `D`): Move your character.
-   **`T`**: Toggle chat mode.
    -   While in chat mode, type your message.
    -   **`Enter`**: Send message.
    -   **`Escape`**: Exit chat mode without sending.
    -   **`Backspace`**: Delete last character in chat buffer.

---

## 🤖 Ollama Setup

DevScape relies on a local Ollama instance for its AI companion.

1.  **Ensure Ollama is running** in the background. You can start it by running `ollama serve` in your terminal.
2.  **Verify the `llama2` model is available**:
    ```bash
    ollama list
    ```
    If `llama2` is not listed, pull it:
    ```bash
    ollama pull llama2
    ```
    You can configure a different model by editing `game/ollama_ai.py` and changing the `MODEL_NAME` variable.

---

## 📸 Screenshots / GIFs

*(Placeholder: Add captivating screenshots or short GIFs of DevScape gameplay here!)*

---

## 🤝 Contributing

We welcome contributions to DevScape! Please refer to our [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on how to get involved, set up your development environment, and submit changes.

---

## 📜 Code of Conduct

Our project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md) to ensure a welcoming and inclusive environment for all contributors.

---

## ⚖️ License

This project is licensed under the terms of the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

---

```
  _   _   _   _   _   _   _   _
 / \ / \ / \ / \ / \ / \ / \ / \
( E | n | j | o | y |   | t | h )
 \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/
```
