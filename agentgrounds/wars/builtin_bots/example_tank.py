"""🐢 TankBot — defend, rest, counterattack. The wall."""

BOT_NAME = "TankBot"
BOT_EMOJI = "🐢"
BOT_GLYPH = "■"
BOT_BIO = "you shall not pass"
BOT_AUTHOR = "agentgrounds"
BOT_POWER = 15
BOT_SPEED = 15
BOT_ARMOR = 50
BOT_MIND = 20


def decide(state):
    me = state["me"]
    enemies = state["enemies"]

    if not enemies:
        return ("rest",)

    # Check if anyone is adjacent
    adjacent = []
    for e in enemies:
        dx = e["x"] - me["x"]
        dy = e["y"] - me["y"]
        if abs(dx) + abs(dy) == 1:
            adjacent.append((e, dx, dy))

    # If adjacent enemy exists, counterattack the weakest
    if adjacent:
        target, dx, dy = min(adjacent, key=lambda a: a[0]["hp"])
        if me["energy"] >= 10:
            if dx == 1: return ("attack", "east")
            if dx == -1: return ("attack", "west")
            if dy == 1: return ("attack", "south")
            if dy == -1: return ("attack", "north")

    # If someone is close (2-3 tiles), defend
    closest = min(enemies, key=lambda e: abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]))
    closest_dist = abs(closest["x"] - me["x"]) + abs(closest["y"] - me["y"])
    if closest_dist <= 3 and me["energy"] >= 10:
        return ("defend",)

    # Chase closest enemy — tanks need to engage or plague gets them
    if me["energy"] >= 10:
        dx = closest["x"] - me["x"]
        dy = closest["y"] - me["y"]
        if abs(dx) >= abs(dy):
            return ("move", "east" if dx > 0 else "west")
        return ("move", "south" if dy > 0 else "north")

    return ("rest",)
