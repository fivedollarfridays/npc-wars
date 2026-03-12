"""🎲 ChaosBot — pure random. Sometimes wins through sheer unpredictability."""

import random

BOT_NAME = "ChaosBot"
BOT_EMOJI = "🎲"
BOT_BIO = "embrace the void"
BOT_AUTHOR = "npcwars"


def decide(state):
    directions = ["north", "south", "east", "west"]
    actions = [
        ("move", random.choice(directions)),
        ("attack", random.choice(directions)),
        ("rest",),
        ("defend",),
    ]
    return random.choice(actions)
