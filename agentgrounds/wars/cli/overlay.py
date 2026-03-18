"""Combat FX overlay for action-phase sub-frames."""
from __future__ import annotations

from agentgrounds.wars.cli.renderer import DEFEND_FX, WEAPON_FX


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
    overlay: dict[tuple[int, int], str] = {}
    for evt in events:
        etype = evt.get("type")
        if etype == "hit":
            _overlay_melee(emoji_pos, evt, overlay)
        elif etype == "miss":
            _overlay_miss(emoji_pos, evt, overlay)
        elif etype in ("ranged_hit", "ranged_miss"):
            _overlay_ranged(emoji_pos, evt, overlay)
        elif etype == "defend":
            _overlay_defend(emoji_pos, evt, overlay)
    return overlay


def _overlay_melee(
    emoji_pos: dict[str, tuple[int, int]],
    evt: dict,
    overlay: dict[tuple[int, int], str],
) -> None:
    atk = emoji_pos.get(evt.get("attacker", ""))
    tgt = emoji_pos.get(evt.get("target", ""))
    if atk and tgt:
        dx = tgt[0] - atk[0]
        dy = tgt[1] - atk[1]
        dist = abs(dx) + abs(dy)
        if dist <= 1:
            overlay[atk] = WEAPON_FX["melee"]
        else:
            sx = 1 if dx > 0 else -1 if dx < 0 else 0
            sy = 1 if dy > 0 else -1 if dy < 0 else 0
            overlay[(atk[0] + sx, atk[1] + sy)] = WEAPON_FX["melee"]


def _overlay_miss(
    emoji_pos: dict[str, tuple[int, int]],
    evt: dict,
    overlay: dict[tuple[int, int], str],
) -> None:
    """Show weapon FX at attacker position for misses (no target on grid)."""
    atk = emoji_pos.get(evt.get("attacker", ""))
    if atk:
        overlay[atk] = WEAPON_FX["melee"]


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
) -> None:
    bot = emoji_pos.get(evt.get("emoji", ""))
    if bot:
        overlay[bot] = DEFEND_FX
