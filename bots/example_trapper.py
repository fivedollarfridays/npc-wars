"""Example trap-using bot -- demonstrates setup(), react(), and trap placement."""

BOT_NAME = "Trapper"
BOT_EMOJI = "🪤"
BOT_GLYPH = "T"
BOT_BIO = "The ground remembers where you walk."
BOT_AUTHOR = "agentgrounds"
BOT_POWER = 35
BOT_SPEED = 20
BOT_ARMOR = 25
BOT_MIND = 20

# spear(8) + reinforced(10) = 18 credits — reach + control
BOT_EQUIPMENT = {
    "weapon": "spear",
    "armor": "reinforced",
    "accessories": [],
    "tactical": None,
}

# Module-level tracking set by setup/react (persists across rounds)
_last_enemy_positions: dict[str, tuple[int, int]] = {}

TRAP_ENERGY_COST = 15
REST_THRESHOLD = 20


def setup(state: dict) -> None:
    """Called once before round 1. Initialize tracking state."""
    _last_enemy_positions.clear()
    for enemy in state.get("enemies", []):
        _last_enemy_positions[enemy["emoji"]] = (enemy["x"], enemy["y"])


def react(state: dict, events: list[dict]) -> None:
    """Called each round with nearby events. Track enemy movement."""
    for enemy in state.get("enemies", []):
        _last_enemy_positions[enemy["emoji"]] = (enemy["x"], enemy["y"])


def _direction_toward(mx: int, my: int, tx: int, ty: int) -> str:
    """Return cardinal direction from (mx,my) toward (tx,ty)."""
    dx = tx - mx
    dy = ty - my
    if abs(dx) >= abs(dy):
        return "east" if dx > 0 else "west"
    return "south" if dy > 0 else "north"


def _manhattan(x1: int, y1: int, x2: int, y2: int) -> int:
    return abs(x1 - x2) + abs(y1 - y2)


def _nearest_enemy(me: dict, enemies: list[dict]) -> dict | None:
    if not enemies:
        return None
    return min(enemies, key=lambda e: _manhattan(me["x"], me["y"], e["x"], e["y"]))


def decide(state: dict) -> tuple:
    me = state["me"]
    enemies = state["enemies"]
    mx, my = me["x"], me["y"]
    energy = me["energy"]
    trap_cooldown = me.get("trap_cooldown", 0)

    # No enemies -- rest
    if not enemies:
        return ("rest",)

    nearest = _nearest_enemy(me, enemies)
    if nearest is None:
        return ("rest",)

    dist = _manhattan(mx, my, nearest["x"], nearest["y"])

    # 1. Adjacent enemy -- attack
    if dist == 1 and energy >= 10:
        return ("attack", _direction_toward(mx, my, nearest["x"], nearest["y"]))

    # 2. Place trap toward nearest enemy if ready
    if trap_cooldown == 0 and energy >= TRAP_ENERGY_COST and dist >= 2:
        direction = _direction_toward(mx, my, nearest["x"], nearest["y"])
        return ("trap", direction)

    # 3. Low energy -- rest
    if energy < REST_THRESHOLD:
        return ("rest",)

    # 4. Move toward nearest enemy
    direction = _direction_toward(mx, my, nearest["x"], nearest["y"])
    return ("move", direction)
