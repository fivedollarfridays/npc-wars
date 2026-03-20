"""Starter bot -- a working foundation with guided TODOs.

Every decision point has a comment explaining what it does
and suggesting alternatives. Tweak the TODOs to make it your own!
"""

import random

BOT_NAME = "Starter"
BOT_EMOJI = "\U0001f31f"
BOT_GLYPH = "◆"
BOT_BIO = "A solid foundation -- tweak the TODOs to make it your own"
BOT_AUTHOR = "agentgrounds"
BOT_POWER = 25
BOT_SPEED = 25
BOT_ARMOR = 25
BOT_MIND = 25

# ── Tuning knobs ────────────────────────────────────────────
# TODO: Change these constants to reshape the bot's personality.
ENERGY_THRESHOLD = 30       # rest when energy drops below this
DENY_HP_THRESHOLD = 40      # attack adjacent enemies below this HP
CHASE_HP_THRESHOLD = 50     # chase enemies below this HP
CHASE_MAX_DIST = 4          # max distance to chase a wounded enemy
CENTER_DRIFT_DIST = 2       # drift toward center when farther than this


def _combat(me):
    """Priorities 3-5: finish kills, deny energy, defend."""
    # PRIORITY 3: Finish kills
    # Adjacent enemy with HP <= our attack power? Kill them.
    # TODO: Change the threshold -- try killing enemies at
    #       50 HP (two hits) by attacking twice in a row.
    #       Or only kill at <= 15 HP to be more conservative.
    if me.can_kill_adjacent() and me.energy >= 10:
        return me.attack(me.weakest_adjacent())

    # PRIORITY 4: Energy denial
    # Low-HP adjacent enemies are probably resting.
    # Attack them -- 25 damage vs their +5 HP heal = brutal.
    # TODO: Try different HP thresholds:
    #   - 30 = only attack very weak resting bots
    #   - 50 = attack anyone who might be resting
    #   - Remove this block entirely to be less aggressive
    for e in me.adjacent_enemies():
        if e["hp"] < DENY_HP_THRESHOLD and me.energy >= 10:
            return me.attack(me.weakest_adjacent())

    # PRIORITY 5: Defend when threatened
    # Defending halves incoming damage (take 15 instead of 25).
    # TODO: Try these alternatives:
    #   - Always defend when ANY enemy is adjacent
    #   - Only defend when 2+ enemies are adjacent
    #   - Never defend -- go full aggro and see what happens
    if me.threatened() and me.energy >= 10:
        return ("defend",)

    return None


def _chase_or_position(me, enemies, state):
    """Priorities 6-8: chase wounded, drift center, idle."""
    # PRIORITY 6: Chase wounded enemies
    # Hunt enemies below 50 HP -- they're easy kills.
    # TODO: Adjust chase behavior:
    #   - Change threshold: 30 (very wounded) vs 70 (slightly hurt)
    #   - Change max chase distance: 3 (close only) vs 6 (across map)
    #   - Target selection: wounded()[0] is closest wounded,
    #     try enemies.weakest() for lowest HP anywhere
    wounded = enemies.wounded(threshold=CHASE_HP_THRESHOLD)
    if wounded:
        target = wounded[0]
        dist = abs(me.x - target["x"]) + abs(me.y - target["y"])
        if dist <= CHASE_MAX_DIST:
            return me.move_toward(target)

    # PRIORITY 7: Positioning -- drift toward center
    # Center position = last to get hit by storm.
    # TODO: Try targeting the WEAKEST enemy instead of center.
    #       Or the CLOSEST enemy. Or stay put and defend.
    #       Positioning strategy changes the whole game feel.
    cx, cy = state["grid_size"] // 2, state["grid_size"] // 2
    if abs(me.x - cx) + abs(me.y - cy) > CENTER_DRIFT_DIST:
        return me.move_toward((cx, cy))

    # PRIORITY 8: Idle behavior -- randomize!
    # When nothing else to do, mix it up. The Watcher boss
    # reads your patterns. Predictable = exploitable.
    # TODO: Try different idle mixes:
    #   - All defend = turtle up (safe but passive)
    #   - All random move = unpredictable (but burns energy)
    #   - Rest only = maximum energy (but The Watcher adapts)
    return random.choice([
        ("defend",),
        ("rest",),
        ("move", random.choice(["north", "south", "east", "west"])),
    ])


def decide(state):
    """Called every round. Uses the helpers DSL for clean code."""
    from agentgrounds.wars.helpers import Me, Enemies, Storm

    me = Me(state)
    enemies = Enemies(state)
    storm = Storm(state)

    # PRIORITY 1: Storm escape
    # The storm deals 10 damage/round. Always flee first.
    # TODO: Try pre-positioning 2 rounds early instead of
    #       reacting. Check storm.border and predict the
    #       next border: if round > 9, border = (round-9)//5
    if storm.danger:
        return me.move_toward(storm.safe_zone_center())

    # PRIORITY 2: Energy management
    # Can't do anything useful below 15 energy.
    # TODO: Experiment with this threshold!
    #   - 15 = aggressive (attack whenever possible)
    #   - 30 = balanced (keep a reserve)
    #   - 50 = conservative (always have options)
    #   Higher thresholds mean more resting, less fighting.
    if me.energy < ENERGY_THRESHOLD:
        return ("rest",)

    # Priorities 3-5: combat (finish kills, deny energy, defend)
    combat_action = _combat(me)
    if combat_action:
        return combat_action

    # Priorities 6-8: chase wounded, position, idle
    return _chase_or_position(me, enemies, state)
