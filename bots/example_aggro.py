"""🤖 AggroBot — pure aggression. Chase closest enemy, attack relentlessly."""

BOT_NAME = "AggroBot"
BOT_EMOJI = "🤖"
BOT_GLYPH = "⚔"
BOT_BIO = "all gas no brakes"
BOT_AUTHOR = "agentgrounds"
BOT_POWER = 40
BOT_SPEED = 20
BOT_ARMOR = 15
BOT_MIND = 25


def decide(state):
    me = state["me"]
    enemies = state["enemies"]

    if not enemies:
        return ("rest",)

    # Find closest enemy
    def dist(e):
        return abs(e["x"] - me["x"]) + abs(e["y"] - me["y"])

    target = min(enemies, key=dist)
    dx = target["x"] - me["x"]
    dy = target["y"] - me["y"]
    d = abs(dx) + abs(dy)

    # If adjacent, always attack
    if d == 1:
        if dx == 1: return ("attack", "east")
        if dx == -1: return ("attack", "west")
        if dy == 1: return ("attack", "south")
        if dy == -1: return ("attack", "north")

    # If out of energy, forced to rest
    if me["energy"] < 5:
        return ("rest",)

    # Chase
    if abs(dx) >= abs(dy):
        return ("move", "east" if dx > 0 else "west")
    else:
        return ("move", "south" if dy > 0 else "north")
