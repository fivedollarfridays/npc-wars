"""🎯 KiteBot — maintain distance, attack once, retreat. Death by a thousand cuts."""

BOT_NAME = "KiteBot"
BOT_EMOJI = "🎯"
BOT_BIO = "catch me if you can"
BOT_AUTHOR = "npcwars"


def _dir_toward(dx, dy):
    if abs(dx) >= abs(dy):
        return "east" if dx > 0 else "west"
    return "south" if dy > 0 else "north"


def _handle_adjacent(dx, dy, energy):
    if energy >= 10:
        if dx == 1: return ("attack", "east")
        if dx == -1: return ("attack", "west")
        if dy == 1: return ("attack", "south")
        if dy == -1: return ("attack", "north")
    if dx == 1: return ("move", "west")
    if dx == -1: return ("move", "east")
    if dy == 1: return ("move", "north")
    return ("move", "south")


def decide(state):
    me = state["me"]
    enemies = state["enemies"]
    grid_size = state["grid_size"]
    if not enemies:
        return ("rest",)
    if me["energy"] < 10:
        return ("rest",)

    def dist(e):
        return abs(e["x"] - me["x"]) + abs(e["y"] - me["y"])

    closest = min(enemies, key=dist)
    dx = closest["x"] - me["x"]
    dy = closest["y"] - me["y"]
    d = abs(dx) + abs(dy)

    if d == 1:
        return _handle_adjacent(dx, dy, me["energy"])
    if d == 2:
        return ("move", _dir_toward(dx, dy))

    # Distance 3+: kite toward center, keep distance ~2-3
    center = grid_size // 2
    cx = center - me["x"]
    cy = center - me["y"]
    if abs(cx) > abs(cy) and abs(cx) > 1:
        return ("move", "east" if cx > 0 else "west")
    if abs(cy) > 1:
        return ("move", "south" if cy > 0 else "north")
    return ("move", _dir_toward(dx, dy))
