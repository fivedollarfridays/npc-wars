"""Knight -- heavily armored tank with a full 4-item loadout.

Demonstrates using all equipment slots: weapon + armor + 2 accessories.
Simple decide: attack adjacent, move toward nearest, rest when low energy.
"""

BOT_NAME = "Knight"
BOT_EMOJI = "\u2694\ufe0f"
BOT_GLYPH = "\u2694"
BOT_BIO = "steel resolve"
BOT_AUTHOR = "agentgrounds"
BOT_POWER = 20
BOT_SPEED = 15
BOT_ARMOR = 40
BOT_MIND = 25

# mace(7) + plate(11) + ring_of_health(4) + charm_of_evasion(5) = 27 credits
BOT_EQUIPMENT = {
    "weapon": "mace",
    "armor": "plate",
    "accessories": ["ring_of_health", "charm_of_evasion"],
    "tactical": None,
}


def _direction_toward(mx: int, my: int, tx: int, ty: int) -> str:
    dx = tx - mx
    dy = ty - my
    if abs(dx) >= abs(dy):
        return "east" if dx > 0 else "west"
    return "south" if dy > 0 else "north"


def _manhattan(x1: int, y1: int, x2: int, y2: int) -> int:
    return abs(x1 - x2) + abs(y1 - y2)


def decide(state: dict) -> tuple:
    me = state["me"]
    enemies = state["enemies"]
    mx, my = me["x"], me["y"]
    energy = me["energy"]

    if not enemies:
        return ("rest",)

    # Find nearest enemy
    nearest = min(enemies, key=lambda e: _manhattan(mx, my, e["x"], e["y"]))
    dist = _manhattan(mx, my, nearest["x"], nearest["y"])

    # Rest when low energy
    if energy < 15:
        return ("rest",)

    # Attack adjacent
    if dist == 1 and energy >= 10:
        return ("attack", _direction_toward(mx, my, nearest["x"], nearest["y"]))

    # Defend when enemies are close (tanky playstyle)
    if dist == 2 and energy >= 10:
        return ("defend",)

    # Move toward nearest enemy
    if energy >= 5:
        return ("move", _direction_toward(mx, my, nearest["x"], nearest["y"]))

    return ("rest",)
