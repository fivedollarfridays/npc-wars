import random

BOT_NAME = "Reaper"
BOT_EMOJI = "💀"
BOT_GLYPH = "☠"
BOT_BIO = "You rest, you die."
BOT_AUTHOR = "agentgrounds"
BOT_POWER = 30
BOT_SPEED = 25
BOT_ARMOR = 20
BOT_MIND = 25

# axe(9) + leather(6) = 15 credits — high-variance death dealer
BOT_EQUIPMENT = {
    "weapon": "axe",
    "armor": "leather",
    "accessories": [],
    "tactical": None,
}


def decide(state):
    from agentgrounds.wars.helpers import Me, Enemies, Storm

    me = Me(state)
    enemies = Enemies(state)
    storm = Storm(state)
    grid = state["grid_size"]

    # --- Storm prediction: where will the border be NEXT round ---
    # Storm is deterministic from round number, so pre-position
    future_danger = storm.active and _near_future_border(me, state, grid)

    # 1. Storm escape — but use FUTURE border, not current
    if storm.danger or future_danger:
        # Can we bump an enemy INTO the storm on the way out?
        for e in me.adjacent_enemies():
            if _push_lands_in_storm(me, e, state, grid):
                return me.move_toward(e)  # bump them stormward
        return me.move_toward(storm.safe_zone_center())

    # 2. Free kill — always take it
    if me.can_kill_adjacent() and me.energy >= 10:
        return me.attack(me.weakest_adjacent())

    # 3. Energy denial — adjacent enemy likely resting? Punish.
    # Enemy energy isn't visible, but low HP enemies often rest to heal.
    for e in me.adjacent_enemies():
        if e["hp"] < 40 and me.energy >= 10:
            return me.attack(me.weakest_adjacent())

    # 4. Defend if threatened — strictly better than counter-attacking
    if me.threatened() and me.energy >= 5:
        return ("defend",)

    # 5. Energy discipline — high threshold
    if me.energy < 40:
        return ("rest",)

    # 6. Hunt wounded — but only if worth the chase
    wounded = enemies.wounded(threshold=50)
    if wounded:
        target = wounded[0]
        # Don't chase across the map burning energy
        dist = abs(me.x - target["x"]) + abs(me.y - target["y"])
        if dist <= 4:
            return me.move_toward(target)

    # 7. Drift center for late-game position
    cx, cy = grid // 2, grid // 2
    if abs(me.x - cx) + abs(me.y - cy) > 2:
        return me.move_toward((cx, cy))

    # 8. IDLE: randomize to defeat The Cringe's PatternTable
    return random.choice([("defend",), ("rest",),
                          ("move", random.choice(["north","south","east","west"]))])


def _near_future_border(me, state, grid):
    """Rough check: will storm reach us in ~2 rounds?"""
    border = state.get("storm_border", 0)
    next_border = border + 1  # conservative estimate
    return (me.x <= next_border or me.x >= grid - 1 - next_border or
            me.y <= next_border or me.y >= grid - 1 - next_border)

def _push_lands_in_storm(me, enemy, state, grid):
    """Would bumping this enemy push them outside safe zone?"""
    border = state.get("storm_border", 0)
    # Direction of push = direction of our movement toward them
    dx = 1 if enemy["x"] > me.x else (-1 if enemy["x"] < me.x else 0)
    dy = 1 if enemy["y"] > me.y else (-1 if enemy["y"] < me.y else 0)
    new_x, new_y = enemy["x"] + dx, enemy["y"] + dy
    return (new_x < border or new_x >= grid - border or
            new_y < border or new_y >= grid - border)
