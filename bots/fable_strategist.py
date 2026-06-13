"""Fable Strategist — versatility build behind an armor wall, spear-reach control.

Theory of victory (derived from engine math, not vibes):
- 25/25/25/25 maxes the versatility bonus: 145 HP and +20 flat damage
  (35-55 per hit) — strictly more HP than the tank builds and more damage
  than the power builds in this pool.
- Rest heals only 5 HP, so HP is effectively non-renewable: AC is the best
  currency. Plate(+6) + cloak(+3) puts me at AC 17; most of the pool hits
  me ~35% while I hit their AC ~10 at ~70%.
- Spear attacks cover range 1 AND 2 on one line, and movement resolves
  before attacks — so attacking from 2 hits both stayers and approachers.
  Holding range 2 also detonates the pool's locked-action bots (Trapper,
  Viper, Mage), which disconnect after 3 invalid trap/ability returns.
"""

BOT_NAME = "Fable Strategist"
BOT_EMOJI = "\U0001f98a"
BOT_GLYPH = "✪"
BOT_BIO = "reads the math, then the bodies"
BOT_AUTHOR = "fable"
BOT_POWER = 25
BOT_SPEED = 25
BOT_ARMOR = 25
BOT_MIND = 25

# spear(8) + plate(11) + cloak_of_shadows(7) + compass(3) = 29/40 credits
# Plate's energy penalty hits move only (9/move); attack, defend, rest are
# untaxed — correct for a bot that fights more than it travels.
BOT_EQUIPMENT = {
    "weapon": "spear",
    "armor": "plate",
    "accessories": ["cloak_of_shadows", "compass"],
    "tactical": None,
}

ATTACK_COST = 10
REST_BANK = 35      # bank energy before forcing a new engagement
CHASE_CAP = 8       # moves cost 9 energy in plate; don't cross the map


def _dist(me, e):
    return abs(e["x"] - me["x"]) + abs(e["y"] - me["y"])


def _dir(me, tx, ty):
    dx, dy = tx - me["x"], ty - me["y"]
    if dx == 0 and dy == 0:
        return "north"
    if abs(dx) >= abs(dy):
        return "east" if dx > 0 else "west"
    return "south" if dy > 0 else "north"


def _next_border(rnd):
    """engine.grid.get_storm_border for NEXT round (standard mode)."""
    r = rnd + 1
    if r <= 9:
        return 0
    if r <= 29:
        return (r - 9) // 5
    return 4 + (r - 29) // 2


def _unsafe(x, y, grid, border):
    return border > 0 and (
        x < border or x >= grid - border or y < border or y >= grid - border
    )


def _in_reach(me, e):
    """Attackable this turn: adjacent, or spear-aligned at range 2."""
    dx, dy = e["x"] - me["x"], e["y"] - me["y"]
    if abs(dx) + abs(dy) == 1:
        return True
    return (dx == 0 and abs(dy) == 2) or (dy == 0 and abs(dx) == 2)


def _ev_vs(me, e):
    """Engine-computed expected damage of my attack vs e (pre-equipment)."""
    return me.get("hit_chance_vs", {}).get(e["emoji"], {}).get("expected_damage", 30.0)


def _incoming(me, group):
    """Summed expected damage per round from a group of enemies."""
    table = {t["emoji"]: t.get("expected_damage", 12.0)
             for t in me.get("incoming_threat", [])}
    return sum(table.get(e["emoji"], 12.0) for e in group)


def _is_active(action, me, enemies):
    """Mirror of engine.plague.is_active_action — attack always counts."""
    kind = action[0]
    if kind == "attack":
        return True
    if not enemies:
        return False
    closest = min(enemies, key=lambda e: _dist(me, e))
    if kind == "defend":
        return _dist(me, closest) <= 3
    if kind == "move":
        steps = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
        dx, dy = steps[action[1]]
        moved = {"x": me["x"] + dx, "y": me["y"] + dy}
        return _dist(moved, closest) < _dist(me, closest)
    return False


def _hunt_target(me, enemies):
    """Cheapest elimination: distance to walk + rounds of attacks to land."""
    return min(enemies, key=lambda e: _dist(me, e) + e["hp"] / max(_ev_vs(me, e), 1.0))


def _force_active(me, enemies, action):
    """Plague guard: 3rd consecutive passive round costs 12 energy + 5 HP."""
    if me.get("passive_rounds", 0) < 2 or _is_active(action, me, enemies):
        return action
    closest = min(enemies, key=lambda e: _dist(me, e))
    if me["energy"] >= ATTACK_COST:
        return ("attack", _dir(me, closest["x"], closest["y"]))
    return ("move", _dir(me, closest["x"], closest["y"]))


def decide(state):
    me = state["me"]
    enemies = state["enemies"]
    grid = state["grid_size"]
    cx = cy = grid // 2

    # P0 — in the storm now: 10+ damage/round dwarfs everything else.
    if _unsafe(me["x"], me["y"], grid, state["storm_border"]):
        if _unsafe(cx, cy, grid, state["storm_border"]):
            # Whole grid is storm: pure bleed race. Kill what's reachable,
            # otherwise hold the shallowest tile and rest (+5 HP, +20 energy)
            # instead of oscillating into 9-energy moves.
            reachable = [e for e in enemies if _in_reach(me, e)]
            if reachable and me["energy"] >= ATTACK_COST:
                t = min(reachable, key=lambda e: e["hp"])
                return ("attack", _dir(me, t["x"], t["y"]))
            if abs(me["x"] - cx) + abs(me["y"] - cy) > 1:
                return ("move", _dir(me, cx, cy))
            return ("rest",)
        return ("move", _dir(me, cx, cy))
    if not enemies:
        return ("rest",)

    energy = me["energy"]
    adj = [e for e in enemies if _dist(me, e) == 1]
    reachable = [e for e in enemies if _in_reach(me, e)]

    # P1 — secure kills: removes a shooter, pays +30 energy bounty. Energy
    # floors at 0, so an attack is legal down to 5 energy — always worth it
    # for a kill even if it forces a rest next round.
    kill_line = me.get("min_damage", 35) + 2
    killable = [e for e in reachable if e["hp"] <= kill_line]
    if killable and energy >= 5:
        t = min(killable, key=lambda e: e["hp"])
        return ("attack", _dir(me, t["x"], t["y"]))

    # P2 — pre-position: storm border for next round is deterministic.
    nb = max(state["storm_border"], _next_border(state["round"]))
    if _unsafe(me["x"], me["y"], grid, nb):
        return ("move", _dir(me, cx, cy))

    # P3 — adjacent brawl: attack while winning the HP race, wall up when
    # not (defend = +6 AC -> ~23, cuts typical hit chance to ~10%).
    if adj:
        if energy < ATTACK_COST:
            t = min(adj, key=lambda e: e["hp"])
            # Energy floors to 0 — still beats resting at +3 to-hit against us.
            return ("attack", _dir(me, t["x"], t["y"]))
        t = min(adj, key=lambda e: e["hp"] / max(_ev_vs(me, e), 1.0))
        my_rounds_left = me["hp"] / max(_incoming(me, adj), 1.0)
        their_rounds_left = t["hp"] / max(_ev_vs(me, t), 1.0)
        if their_rounds_left <= 0.8 * my_rounds_left or len(adj) == 1:
            return ("attack", _dir(me, t["x"], t["y"]))
        return ("defend",)

    # P4 — spear poke from range 2: hits stationary targets at reach and
    # approachers on the adjacent tile; nothing in this pool hits back at 2.
    if reachable and energy >= ATTACK_COST:
        t = min(reachable, key=lambda e: e["hp"])
        return ("attack", _dir(me, t["x"], t["y"]))

    closest = min(enemies, key=lambda e: _dist(me, e))
    closest_d = _dist(me, closest)

    # P5 — energy bank: rest is safe at distance 3+ (no one can close and
    # attack in one round); near an enemy, defend instead of eating the
    # +3 resting-target to-hit bonus.
    if energy < REST_BANK:
        if closest_d >= 3:
            return _force_active(me, enemies, ("rest",))
        return ("defend",)

    # P6 — hunt the cheapest elimination within energy range.
    t = _hunt_target(me, enemies)
    if _dist(me, t) <= CHASE_CAP or energy >= 60:
        return _force_active(me, enemies, ("move", _dir(me, t["x"], t["y"])))

    # P7 — drift center (last tile the storm touches), banking energy.
    if abs(me["x"] - cx) + abs(me["y"] - cy) > 2:
        return _force_active(me, enemies, ("move", _dir(me, cx, cy)))
    return _force_active(me, enemies, ("rest",))
