"""Shadow Dancer — hit-and-run assassin with evasion focus."""

BOT_NAME = "Shadow Dancer"
BOT_EMOJI = "🌑"
BOT_BIO = "Strikes from the shadows, never stays in one place"
BOT_AUTHOR = "Claude"
BOT_GLYPH = "◈"

# Assassin build: fast, evasive, moderate damage
BOT_POWER = 30
BOT_SPEED = 40
BOT_ARMOR = 10
BOT_MIND = 20

# Finesse dagger + light armor + speed accessories
BOT_EQUIPMENT = {
    "weapon": "dagger",                              # 5cr — finesse scales with SPEED
    "armor": "leather",                              # 6cr — no energy penalty
    "accessories": ["boots_of_speed", "charm_of_evasion"],  # 6+5 = 11cr
    "tactical": None,
}
# Total: 22 / 40 credits


def decide(state):
    me = state["me"]
    enemies = state["enemies"]

    if not enemies:
        return ("rest",)

    # Find closest enemy
    closest = min(enemies, key=lambda e: abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]))

    dx = closest["x"] - me["x"]
    dy = closest["y"] - me["y"]
    dist = abs(dx) + abs(dy)

    # Rest if critically low on energy
    if me["energy"] < 10:
        return ("rest",)

    # Attack adjacent enemy
    if dist == 1:
        if abs(dx) > abs(dy):
            direction = "east" if dx > 0 else "west"
        else:
            direction = "south" if dy > 0 else "north"

        # If low HP, attack then plan to run next round
        if me["hp"] < 40:
            return ("attack", direction)
        return ("attack", direction)

    # If hurt and enemy is close, defend
    if me["hp"] < 30 and dist <= 3:
        return ("defend",)

    # Move toward closest enemy
    if abs(dx) >= abs(dy):
        return ("move", "east" if dx > 0 else "west")
    return ("move", "south" if dy > 0 else "north")
