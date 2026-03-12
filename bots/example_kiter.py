"""🎯 KiteBot — maintain distance, attack once, retreat. Death by a thousand cuts."""

BOT_NAME = "KiteBot"
BOT_EMOJI = "🎯"
BOT_BIO = "catch me if you can"
BOT_AUTHOR = "npcwars"


def decide(state):
    me = state["me"]
    enemies = state["enemies"]
    grid_size = state["grid_size"]
    storm_border = state["storm_border"]

    if not enemies:
        return ("rest",)

    if me["energy"] < 10:
        return ("rest",)

    # Find closest enemy
    def dist(e):
        return abs(e["x"] - me["x"]) + abs(e["y"] - me["y"])

    closest = min(enemies, key=dist)
    dx = closest["x"] - me["x"]
    dy = closest["y"] - me["y"]
    d = abs(dx) + abs(dy)

    # If adjacent: attack then next round we'll retreat
    if d == 1:
        if me["energy"] >= 15:
            if dx == 1: return ("attack", "east")
            if dx == -1: return ("attack", "west")
            if dy == 1: return ("attack", "south")
            if dy == -1: return ("attack", "north")
        # Low energy, run
        if dx == 1: return ("move", "west")
        if dx == -1: return ("move", "east")
        if dy == 1: return ("move", "north")
        if dy == -1: return ("move", "south")

    # If distance 2: approach to attack range
    if d == 2:
        if abs(dx) >= abs(dy):
            return ("move", "east" if dx > 0 else "west")
        else:
            return ("move", "south" if dy > 0 else "north")

    # If distance 3+: kite toward center, keep distance ~2-3
    center = grid_size // 2
    cx = center - me["x"]
    cy = center - me["y"]

    # Prefer moving toward center
    if abs(cx) > abs(cy) and abs(cx) > 1:
        return ("move", "east" if cx > 0 else "west")
    elif abs(cy) > 1:
        return ("move", "south" if cy > 0 else "north")

    # If at center, slowly approach closest enemy
    if abs(dx) >= abs(dy):
        return ("move", "east" if dx > 0 else "west")
    else:
        return ("move", "south" if dy > 0 else "north")
