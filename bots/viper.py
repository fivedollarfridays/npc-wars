import random

BOT_NAME = "Viper"
BOT_EMOJI = "🐍"
BOT_BIO = "Patient counter-puncher. Kites, traps, and strikes when the math says yes."
BOT_GLYPH = "◆"

# Sustain build: enough power to kill, high mind for energy war, decent armor for HP pool
BOT_POWER = 25
BOT_SPEED = 20
BOT_ARMOR = 20
BOT_MIND = 35

BOT_EQUIPMENT = {
    "weapon": "spear",          # 8 credits - reach attack at 2 tiles, great for kiting
    "armor": "reinforced",      # 10 credits - +3 DR, only -1 energy penalty
    "accessories": [
        "pendant_of_mind",      # 4 credits - +10 max energy, +2 regen
        "ring_of_haste",        # 5 credits - +2 initiative, -1 energy cost
    ],
    "tactical": None,
}
# Total: 27 / 40 credits (lean loadout, stats do the work)

# persistent state across rounds
_tracked = {}
_last_positions = {}
_trap_tiles = set()


def setup(state):
    global _tracked, _last_positions, _trap_tiles
    _tracked = {}
    _last_positions = {}
    _trap_tiles = set()


def on_kill(state, victim_emoji):
    global _tracked
    if victim_emoji in _tracked:
        del _tracked[victim_emoji]


def react(state, events):
    pass


def _manhattan(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


def _direction_toward(mx, my, tx, ty):
    dx = tx - mx
    dy = ty - my
    if abs(dx) >= abs(dy):
        return "east" if dx > 0 else "west"
    return "south" if dy > 0 else "north"


def _direction_away(mx, my, tx, ty):
    dx = mx - tx
    dy = my - ty
    if abs(dx) >= abs(dy):
        return "east" if dx > 0 else "west"
    return "south" if dy > 0 else "north"


def _storm_safe(x, y, state):
    border = state.get("storm_border", 0)
    gs = state["grid_size"]
    return border <= x < gs - border and border <= y < gs - border


def _next_pos(x, y, direction):
    deltas = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
    dx, dy = deltas.get(direction, (0, 0))
    return x + dx, y + dy


def _tile_occupied(x, y, enemies):
    return any(e["x"] == x and e["y"] == y for e in enemies)


def _safe_move_toward(mx, my, tx, ty, state, enemies):
    preferred = _direction_toward(mx, my, tx, ty)
    nx, ny = _next_pos(mx, my, preferred)
    gs = state["grid_size"]
    if 0 <= nx < gs and 0 <= ny < gs and _storm_safe(nx, ny, state):
        return ("move", preferred)
    # try perpendicular directions
    alts = [d for d in ["north", "south", "east", "west"] if d != preferred]
    random.shuffle(alts)
    for d in alts:
        nx, ny = _next_pos(mx, my, d)
        if 0 <= nx < gs and 0 <= ny < gs and _storm_safe(nx, ny, state):
            return ("move", d)
    return ("move", preferred)


def _get_adjacent_dir(mx, my, ex, ey):
    if ex == mx and ey == my - 1: return "north"
    if ex == mx and ey == my + 1: return "south"
    if ex == mx + 1 and ey == my: return "east"
    if ex == mx - 1 and ey == my: return "west"
    return None


def _get_reach_dir(mx, my, ex, ey):
    """Check if enemy is exactly 2 tiles away in a cardinal direction (spear reach)."""
    if ex == mx and ey == my - 2: return "north"
    if ex == mx and ey == my + 2: return "south"
    if ex == mx + 2 and ey == my: return "east"
    if ex == mx - 2 and ey == my: return "west"
    return None


def decide(state):
    global _last_positions, _trap_tiles

    me = state["me"]
    mx, my = me["x"], me["y"]
    hp, energy = me["hp"], me["energy"]
    max_hp = me.get("max_hp", 145)
    enemies = state["enemies"]
    gs = state["grid_size"]
    rnd = state["round"]
    border = state.get("storm_border", 0)
    hit_vs = me.get("hit_chance_vs", {})
    trap_cd = me.get("trap_cooldown", 99)
    unlocked = me.get("unlocked_actions", [])

    if not enemies:
        return ("rest",)

    # track enemy movement patterns
    for e in enemies:
        em = e["emoji"]
        prev = _last_positions.get(em)
        if prev:
            _tracked[em] = {
                "dx": e["x"] - prev[0],
                "dy": e["y"] - prev[1],
            }
        _last_positions[em] = (e["x"], e["y"])

    # adjacency info
    adjacent = []
    reach_targets = []
    for e in enemies:
        d = _manhattan(mx, my, e["x"], e["y"])
        adj_dir = _get_adjacent_dir(mx, my, e["x"], e["y"])
        reach_dir = _get_reach_dir(mx, my, e["x"], e["y"])
        if adj_dir:
            adjacent.append((e, adj_dir))
        if reach_dir:
            reach_targets.append((e, reach_dir))

    # find leader
    leader = None
    for e in enemies:
        if e.get("is_leader"):
            leader = e
            break

    # ---------- PRIORITY 1: escape storm ----------
    if not _storm_safe(mx, my, state):
        cx, cy = gs // 2, gs // 2
        return _safe_move_toward(mx, my, cx, cy, state, enemies)

    # preemptive storm dodge: if storm will close next round, move now
    future_border = border
    if rnd >= 9:
        if rnd < 29:
            future_border = max(border, (rnd + 1 - 9) // 5)
        else:
            future_border = max(border, border + 1)
    if not (future_border <= mx < gs - future_border and future_border <= my < gs - future_border):
        cx, cy = gs // 2, gs // 2
        return _safe_move_toward(mx, my, cx, cy, state, enemies)

    # ---------- PRIORITY 2: rest when broke ----------
    if energy < 15:
        # if adjacent enemy, try to move away first if we have 5 energy
        if adjacent and energy >= 5:
            e, _ = adjacent[0]
            d = _direction_away(mx, my, e["x"], e["y"])
            nx, ny = _next_pos(mx, my, d)
            if 0 <= nx < gs and 0 <= ny < gs and _storm_safe(nx, ny, state):
                return ("move", d)
        return ("rest",)

    # ---------- PRIORITY 3: finish kills (adjacent) ----------
    min_dmg = me.get("min_damage", 22)
    for e, d in adjacent:
        if e["hp"] <= min_dmg and energy >= 10:
            return ("attack", d)

    # ---------- PRIORITY 3b: finish kills (spear reach at 2 tiles) ----------
    for e, d in reach_targets:
        if e["hp"] <= min_dmg * 0.6 and energy >= 10:
            return ("attack", d)

    # ---------- PRIORITY 4: energy denial - attack low HP adjacent (likely resting) ----------
    for e, d in adjacent:
        if e["hp"] < 40 and energy >= 10:
            return ("attack", d)

    # ---------- PRIORITY 5: defend when threatened at low HP ----------
    if adjacent and hp < max_hp * 0.35 and energy >= 10:
        return ("defend",)

    # ---------- PRIORITY 5b: kite - if adjacent and we have energy, retreat + trap ----------
    if adjacent and energy >= 20 and hp < max_hp * 0.5:
        strongest_adj = max(adjacent, key=lambda x: x[0]["hp"])
        e = strongest_adj[0]
        away_dir = _direction_away(mx, my, e["x"], e["y"])
        # place trap behind us (toward enemy) as we retreat
        toward_dir = _direction_toward(mx, my, e["x"], e["y"])
        if "trap" in unlocked and trap_cd == 0 and energy >= 35:
            _trap_tiles.add(_next_pos(mx, my, toward_dir))
            return ("trap", toward_dir)
        nx, ny = _next_pos(mx, my, away_dir)
        if 0 <= nx < gs and 0 <= ny < gs and _storm_safe(nx, ny, state):
            return ("move", away_dir)

    # ---------- PRIORITY 6: attack adjacent with good hit chance ----------
    for e, d in adjacent:
        em = e["emoji"]
        info = hit_vs.get(em, {})
        hit_chance = info.get("hit_chance", 50)
        if hit_chance >= 55 and energy >= 10:
            return ("attack", d)

    # ---------- PRIORITY 6b: spear reach attacks on wounded targets ----------
    for e, d in reach_targets:
        em = e["emoji"]
        info = hit_vs.get(em, {})
        if e["hp"] < 60 and energy >= 10:
            return ("attack", d)

    # ---------- PRIORITY 7: trap placement (predictive) ----------
    if "trap" in unlocked and trap_cd == 0 and energy >= 25:
        # place trap toward closest enemy predicted position
        closest = min(enemies, key=lambda e: _manhattan(mx, my, e["x"], e["y"]))
        dist = _manhattan(mx, my, closest["x"], closest["y"])
        if 2 <= dist <= 4:
            d = _direction_toward(mx, my, closest["x"], closest["y"])
            trap_pos = _next_pos(mx, my, d)
            if 0 <= trap_pos[0] < gs and 0 <= trap_pos[1] < gs:
                _trap_tiles.add(trap_pos)
                return ("trap", d)

    # ---------- PRIORITY 8: hunt leader for bounty ----------
    if leader and not me.get("is_leader"):
        dist = _manhattan(mx, my, leader["x"], leader["y"])
        if dist <= 5 and energy >= 25 and hp > max_hp * 0.4:
            return _safe_move_toward(mx, my, leader["x"], leader["y"], state, enemies)

    # ---------- PRIORITY 9: chase wounded ----------
    wounded = [e for e in enemies if e["hp"] < 50]
    if wounded and energy >= 20:
        target = min(wounded, key=lambda e: _manhattan(mx, my, e["x"], e["y"]))
        dist = _manhattan(mx, my, target["x"], target["y"])
        if dist <= 5:
            return _safe_move_toward(mx, my, target["x"], target["y"], state, enemies)

    # ---------- PRIORITY 10: heal up if safe ----------
    if hp < max_hp * 0.7 and not adjacent and energy >= 20:
        return ("rest",)

    # ---------- PRIORITY 11: drift toward center ----------
    cx, cy = gs // 2, gs // 2
    if _manhattan(mx, my, cx, cy) > 2:
        return _safe_move_toward(mx, my, cx, cy, state, enemies)

    # ---------- PRIORITY 12: randomize idle ----------
    choices = [("defend",), ("rest",)]
    dirs = ["north", "south", "east", "west"]
    safe_dirs = []
    for d in dirs:
        nx, ny = _next_pos(mx, my, d)
        if 0 <= nx < gs and 0 <= ny < gs and _storm_safe(nx, ny, state):
            safe_dirs.append(d)
    if safe_dirs:
        choices.append(("move", random.choice(safe_dirs)))
    return random.choice(choices)
