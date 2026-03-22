"""Example ability-using bot -- demonstrates power_up, evolve, and use_ability."""

BOT_NAME = "Mage"
BOT_EMOJI = "\U0001f52e"
BOT_GLYPH = "\u2726"
BOT_BIO = "Arcane power channeled through crystal armor"
BOT_AUTHOR = "agentgrounds"

BOT_POWER = 15
BOT_SPEED = 20
BOT_ARMOR = 20
BOT_MIND = 45

# bow(6) + crystal(14) + pendant_of_mind(4) + amulet_of_crit(6) = 30/40 credits
BOT_EQUIPMENT = {
    "weapon": "bow",
    "armor": "crystal",
    "accessories": ["pendant_of_mind", "amulet_of_crit"],
    "tactical": None,
}


def power_up(state):
    """Define a damage ability -- Arcane Bolt."""
    return {
        "name": "Arcane Bolt",
        "type": "damage",
        "potency": 25,
        "range": 2,
        "cooldown": 4,
        "energy_cost": 20,
    }


def evolve(state):
    """Boost ability potency and shift stats toward mind at 3 kills or round 20."""
    return {
        "ability_boost": 10,
        "stat_shift": {"mind": 5, "armor": -5},
    }


def setup(state):
    """Pre-match initialization (no-op for mage)."""
    pass


def react(state, events):
    """Track nearby combat events (no-op for mage)."""
    pass


def _direction_toward(mx, my, tx, ty):
    """Return cardinal direction from (mx,my) toward (tx,ty)."""
    dx = tx - mx
    dy = ty - my
    if abs(dx) >= abs(dy):
        return "east" if dx > 0 else "west"
    return "south" if dy > 0 else "north"


def _manhattan(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


def decide(state):
    me = state["me"]
    enemies = state["enemies"]

    if not enemies:
        return ("rest",)

    mx, my = me["x"], me["y"]
    energy = me["energy"]

    # Use ability when ready and enemy in range
    ability = me.get("ability")
    if ability and ability.get("cooldown_remaining", 1) == 0 and energy >= 20:
        closest = min(enemies, key=lambda e: _manhattan(mx, my, e["x"], e["y"]))
        dist = _manhattan(mx, my, closest["x"], closest["y"])
        if dist <= 2:
            direction = _direction_toward(mx, my, closest["x"], closest["y"])
            return ("use_ability", direction)

    # Rest if low energy
    if energy < 15:
        return ("rest",)

    # Find nearest enemy
    closest = min(enemies, key=lambda e: _manhattan(mx, my, e["x"], e["y"]))
    dist = _manhattan(mx, my, closest["x"], closest["y"])

    # Attack adjacent
    if dist == 1 and energy >= 10:
        return ("attack", _direction_toward(mx, my, closest["x"], closest["y"]))

    # Move toward nearest
    if energy >= 5:
        return ("move", _direction_toward(mx, my, closest["x"], closest["y"]))

    return ("rest",)
