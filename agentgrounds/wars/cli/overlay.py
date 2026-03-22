"""Combat FX overlay for action-phase sub-frames."""
from __future__ import annotations

from agentgrounds.wars.cli.renderer import DEFEND_FX, WEAPON_FX

TRAP_FX = "\U0001f4a5"
TACTICAL_FX = "\u26a1"
ABILITY_FX = "\U0001f52e"
EVOLVE_FX = "\U0001f9ec"

# ANSI codes for aura effects
_RST = "\033[0m"
_BOLD = "\033[1m"
_RED = "\033[31m"
_YELLOW = "\033[33m"

_ADJACENTS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def build_combat_overlay(
    positions: list[dict],
    events: list[dict],
) -> dict[tuple[int, int], str]:
    """Build an overlay dict of FX indicators for combat events.

    Returns a mapping from (x, y) grid coordinates to the FX indicator string
    that should be rendered at that cell during the action sub-frame.
    """
    emoji_pos: dict[str, tuple[int, int]] = {
        p["emoji"]: (p["x"], p["y"]) for p in positions if p["alive"]
    }
    # Pre-compute kill victims and hit targets for upgrade logic
    kill_victims = _kill_victims(events)
    hit_targets = _hit_targets(events)

    overlay: dict[tuple[int, int], str] = {}
    for evt in events:
        etype = evt.get("type")
        if etype == "hit":
            _overlay_melee(emoji_pos, evt, overlay, kill_victims)
        elif etype == "miss":
            _overlay_miss(emoji_pos, evt, overlay)
        elif etype in ("ranged_hit", "ranged_miss"):
            _overlay_ranged(emoji_pos, evt, overlay)
        elif etype == "defend":
            _overlay_defend(emoji_pos, evt, overlay, hit_targets)
        elif etype == "trap_trigger":
            _overlay_trap_trigger(evt, overlay)
        elif etype == "tactical_activate":
            _overlay_tactical(emoji_pos, evt, overlay)
        elif etype == "ability_damage":
            _overlay_ability_damage(emoji_pos, evt, overlay)
        elif etype == "evolve":
            _overlay_evolve(emoji_pos, evt, overlay)
    return overlay


def _overlay_melee(
    emoji_pos: dict[str, tuple[int, int]],
    evt: dict,
    overlay: dict[tuple[int, int], str],
    kill_victims: frozenset[str],
) -> None:
    atk = emoji_pos.get(evt.get("attacker", ""))
    tgt = emoji_pos.get(evt.get("target", ""))
    target_emoji = evt.get("target", "")
    fx = WEAPON_FX["kill"] if target_emoji in kill_victims else WEAPON_FX["melee"]
    if atk and tgt:
        dx = tgt[0] - atk[0]
        dy = tgt[1] - atk[1]
        dist = abs(dx) + abs(dy)
        if dist <= 1:
            overlay[atk] = fx
        else:
            sx = 1 if dx > 0 else -1 if dx < 0 else 0
            sy = 1 if dy > 0 else -1 if dy < 0 else 0
            overlay[(atk[0] + sx, atk[1] + sy)] = fx


def _overlay_miss(
    emoji_pos: dict[str, tuple[int, int]],
    evt: dict,
    overlay: dict[tuple[int, int], str],
) -> None:
    """Show miss FX at attacker position for misses (no target on grid)."""
    atk = emoji_pos.get(evt.get("attacker", ""))
    if atk:
        overlay[atk] = WEAPON_FX["miss"]


def _overlay_ranged(
    emoji_pos: dict[str, tuple[int, int]],
    evt: dict,
    overlay: dict[tuple[int, int], str],
) -> None:
    atk = emoji_pos.get(evt.get("attacker", ""))
    tgt = emoji_pos.get(evt.get("target", ""))
    if atk and tgt:
        mid = ((atk[0] + tgt[0]) // 2, (atk[1] + tgt[1]) // 2)
        overlay[mid] = WEAPON_FX["ranged"]


def _overlay_defend(
    emoji_pos: dict[str, tuple[int, int]],
    evt: dict,
    overlay: dict[tuple[int, int], str],
    hit_targets: frozenset[str],
) -> None:
    bot_emoji = evt.get("emoji", "")
    bot = emoji_pos.get(bot_emoji)
    if bot:
        fx = WEAPON_FX["defend_block"] if bot_emoji in hit_targets else DEFEND_FX
        overlay[bot] = fx


def _overlay_trap_trigger(
    evt: dict,
    overlay: dict[tuple[int, int], str],
) -> None:
    """Place explosion FX at the trap trigger coordinates."""
    x = evt.get("x")
    y = evt.get("y")
    if x is not None and y is not None:
        overlay[(int(x), int(y))] = TRAP_FX


def _overlay_tactical(
    emoji_pos: dict[str, tuple[int, int]],
    evt: dict,
    overlay: dict[tuple[int, int], str],
) -> None:
    """Place lightning FX on tactical activator's tile."""
    pos = emoji_pos.get(evt.get("emoji", ""))
    if pos:
        overlay[pos] = TACTICAL_FX


def _overlay_ability_damage(
    emoji_pos: dict[str, tuple[int, int]],
    evt: dict,
    overlay: dict[tuple[int, int], str],
) -> None:
    """Place crystal ball FX on ability damage target's tile."""
    pos = emoji_pos.get(evt.get("target", ""))
    if pos:
        overlay[pos] = ABILITY_FX


def _overlay_evolve(
    emoji_pos: dict[str, tuple[int, int]],
    evt: dict,
    overlay: dict[tuple[int, int], str],
) -> None:
    """Place DNA FX on evolved bot's tile."""
    pos = emoji_pos.get(evt.get("emoji", ""))
    if pos:
        overlay[pos] = EVOLVE_FX


def _kill_victims(events: list[dict]) -> frozenset[str]:
    """Return set of emojis that appear as kill victims this round."""
    return frozenset(
        evt.get("victim", "") for evt in events if evt.get("type") == "kill"
    )


def _hit_targets(events: list[dict]) -> frozenset[str]:
    """Return set of emojis that appear as hit targets this round."""
    return frozenset(
        evt.get("target", "") for evt in events if evt.get("type") == "hit"
    )


def build_aura_overlay(
    positions: list[dict],
    grid_size: int,
    storm_border: int,
) -> dict[tuple[int, int], str]:
    """Build overlay of colored dots around tier 3+ bots.

    Tier 3: dim yellow dot on adjacent empty cells.
    Tier 4: bold red dot on adjacent empty cells.
    """
    occupied: set[tuple[int, int]] = {
        (p["x"], p["y"]) for p in positions if p["alive"]
    }
    overlay: dict[tuple[int, int], str] = {}
    for p in positions:
        if not p["alive"] or p.get("momentum_tier", 0) < 3:
            continue
        tier = p["momentum_tier"]
        dot = f"{_YELLOW}\u00b7{_RST}" if tier == 3 else f"{_BOLD}{_RED}\u00b7{_RST}"
        bx, by = p["x"], p["y"]
        for dx, dy in _ADJACENTS:
            nx, ny = bx + dx, by + dy
            if nx < 0 or ny < 0 or nx >= grid_size or ny >= grid_size:
                continue
            if nx < storm_border or ny < storm_border:
                continue
            if nx >= grid_size - storm_border or ny >= grid_size - storm_border:
                continue
            if (nx, ny) in occupied:
                continue
            overlay[(nx, ny)] = dot

    # Leader gold diamond on first available adjacent empty cell
    for p in positions:
        if not p["alive"] or not p.get("is_leader", False):
            continue
        bx, by = p["x"], p["y"]
        for dx, dy in _ADJACENTS:
            nx, ny = bx + dx, by + dy
            if 0 <= nx < grid_size and 0 <= ny < grid_size:
                if (nx, ny) not in occupied:
                    overlay[(nx, ny)] = f"{_YELLOW}\u2666{_RST}"
                    break

    return overlay
