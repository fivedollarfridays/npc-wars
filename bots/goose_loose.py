"""🪿 GooseLoose — the founder bot. Balanced hunter that chases wounded enemies."""

import math

BOT_NAME = "GooseLoose"
BOT_EMOJI = "🪿"
BOT_BIO = "the goose is loose"
BOT_AUTHOR = "kmasty"


def decide(state):
    me = state["me"]
    enemies = state["enemies"]
    grid_size = state["grid_size"]
    storm_border = state["storm_border"]

    if not enemies:
        return ("rest",)

    # Find closest wounded enemy (prefer low HP targets)
    def enemy_score(e):
        dist = abs(e["x"] - me["x"]) + abs(e["y"] - me["y"])
        return e["hp"] + dist * 5  # Prefer close + wounded

    target = min(enemies, key=enemy_score)
    dx = target["x"] - me["x"]
    dy = target["y"] - me["y"]
    dist = abs(dx) + abs(dy)

    # If low energy, rest up
    if me["energy"] < 20:
        return ("rest",)

    # If low HP and not cornered, defend
    if me["hp"] < 30 and dist <= 2:
        return ("defend",)

    # If adjacent, attack
    if dist == 1:
        if dx == 1:
            return ("attack", "east")
        elif dx == -1:
            return ("attack", "west")
        elif dy == 1:
            return ("attack", "south")
        elif dy == -1:
            return ("attack", "north")

    # Move toward target, but prefer staying near center to avoid storm
    center = grid_size // 2
    cx_pull = center - me["x"]
    cy_pull = center - me["y"]

    # If storm is active and we're near edge, prioritize moving to center
    if storm_border > 0:
        if me["x"] < storm_border + 1 or me["x"] >= grid_size - storm_border - 1:
            dx = cx_pull
        if me["y"] < storm_border + 1 or me["y"] >= grid_size - storm_border - 1:
            dy = cy_pull

    # Move toward target
    if abs(dx) >= abs(dy):
        return ("move", "east" if dx > 0 else "west")
    else:
        return ("move", "south" if dy > 0 else "north")
