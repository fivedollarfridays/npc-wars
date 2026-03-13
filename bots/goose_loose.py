"""🪿 GooseLoose — the founder bot. Balanced hunter that chases wounded enemies."""

import math

BOT_NAME = "GooseLoose"
BOT_EMOJI = "🪿"
BOT_BIO = "the goose is loose"
BOT_AUTHOR = "kmasty"


def _attack_adjacent(dx, dy):
    """Return attack action for an adjacent enemy, or None."""
    if dx == 1:
        return ("attack", "east")
    if dx == -1:
        return ("attack", "west")
    if dy == 1:
        return ("attack", "south")
    if dy == -1:
        return ("attack", "north")
    return None


def _apply_storm_pull(dx, dy, me, grid_size, storm_border):
    """Adjust dx/dy toward center when near storm edge. Only overrides if pull is non-zero."""
    center = grid_size // 2
    cx_pull = center - me["x"]
    cy_pull = center - me["y"]
    if me["x"] < storm_border + 1 or me["x"] >= grid_size - storm_border - 1:
        if cx_pull != 0:
            dx = cx_pull
    if me["y"] < storm_border + 1 or me["y"] >= grid_size - storm_border - 1:
        if cy_pull != 0:
            dy = cy_pull
    return dx, dy


def decide(state):
    me = state["me"]
    enemies = state["enemies"]
    grid_size = state["grid_size"]
    storm_border = state["storm_border"]

    if not enemies:
        return ("rest",)

    # Find closest wounded enemy (prefer low HP targets)
    target = min(enemies, key=lambda e: e["hp"] + (abs(e["x"] - me["x"]) + abs(e["y"] - me["y"])) * 5)
    dx = target["x"] - me["x"]
    dy = target["y"] - me["y"]
    dist = abs(dx) + abs(dy)

    if me["energy"] < 20:
        return ("rest",)

    if me["hp"] < 30 and dist <= 2:
        return ("defend",)

    if dist == 1:
        attack = _attack_adjacent(dx, dy)
        if attack:
            return attack

    # Apply storm pull when storm is active
    if storm_border > 0:
        dx, dy = _apply_storm_pull(dx, dy, me, grid_size, storm_border)

    # Move toward target (or center if storm-pulled)
    if abs(dx) >= abs(dy):
        return ("move", "east" if dx > 0 else "west")
    return ("move", "south" if dy > 0 else "north")
