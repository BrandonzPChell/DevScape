"""
run_game.py — A ceremonial gate to launch DevScape.

This script allows stewards to enter the shrine with a single command:
    python run_game.py
"""

import os
import sys

# Ensure the game package is discoverable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from game.main import Game


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
