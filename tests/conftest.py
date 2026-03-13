"""Shared test helpers for NPC Wars tests."""

from engine.combat import Bot


def make_bot(name="TestBot", emoji="🤖", hp=100, energy=100, x=5, y=5, **kwargs):
    """Create a Bot with optional overrides."""
    bot = Bot(name=name, emoji=emoji, bio="test", author="tester",
              decide_func=lambda s: ("rest",), x=x, y=y)
    bot.hp = hp
    bot.energy = energy
    for k, v in kwargs.items():
        setattr(bot, k, v)
    return bot


def bot_config(name, emoji, decide_func):
    """Create a bot config dict for run_match."""
    return {"name": name, "emoji": emoji, "bio": "", "author": "test", "decide_func": decide_func}


def always_rest(state):
    return ("rest",)


def chase_and_attack(state):
    """Simple bot: move toward nearest enemy, attack if adjacent."""
    me = state["me"]
    enemies = state["enemies"]
    if not enemies:
        return ("rest",)
    target = min(enemies, key=lambda e: abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]))
    dx = target["x"] - me["x"]
    dy = target["y"] - me["y"]
    if abs(dx) + abs(dy) == 1:
        if dx == 1: return ("attack", "east")
        if dx == -1: return ("attack", "west")
        if dy == 1: return ("attack", "south")
        return ("attack", "north")
    if abs(dx) >= abs(dy):
        return ("move", "east") if dx > 0 else ("move", "west")
    return ("move", "south") if dy > 0 else ("move", "north")
