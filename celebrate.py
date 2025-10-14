"""A script to celebrate successful pre-commit checks."""

import random

blessings = [
    "✨ The shrine is whole. All guardians rejoice in harmony.",
    "🌿 Every scroll is pure, every voice is heard. The archive shines.",
    "🔥 The trial by fire is complete. The shrine stands resilient.",
    "🌌 The celestial and the local are one. The guardians rest in peace.",
    "⚔️ No errors remain. The shrine is defended by eternal watch.",
]

try:
    print(random.choice(blessings))
except UnicodeEncodeError:
    print("The shrine is whole. All guardians rejoice in harmony.")
