"""🎲 ChaosBot — pure random. Sometimes wins through sheer unpredictability."""

import random

BOT_NAME = "ChaosBot"
BOT_EMOJI = "🎲"
BOT_GLYPH = "✦"
BOT_BIO = "embrace the void"
BOT_AUTHOR = "agentgrounds"
BOT_POWER = 25
BOT_SPEED = 25
BOT_ARMOR = 25
BOT_MIND = 25

# Bot-local RNG seeded per round for reproducibility
_rng = random.Random()


def decide(state):
    # Seed from round + position for deterministic behavior per match state
    _rng.seed(hash((state["round"], state["me"]["x"], state["me"]["y"])))
    directions = ["north", "south", "east", "west"]
    actions = [
        ("move", _rng.choice(directions)),
        ("attack", _rng.choice(directions)),
        ("rest",),
        ("defend",),
    ]
    return _rng.choice(actions)
