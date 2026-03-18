"""Preset strategy code generation for NPC Wars bots.

Generates Python source code for bot decide() function bodies
based on playstyle presets and tuning sliders.
"""

from __future__ import annotations

from collections.abc import Callable

__all__ = ["PRESET_NAMES", "generate_preset"]

PRESET_NAMES: tuple[str, ...] = ("aggro", "tank", "kiter", "opportunist", "chaos")

_PREAMBLE = [
    "from agentgrounds.wars.helpers import Me, Enemies, Storm",
    "me = Me(state)",
    "enemies = Enemies(state)",
    "storm = Storm(state)",
    "if storm.danger:",
    "    return me.flee_storm()",
]


def _validate_slider(name: str, value: int) -> None:
    """Raise ValueError if slider is outside 1-10 range."""
    if not (1 <= value <= 10):
        raise ValueError(f"{name} must be between 1 and 10, got {value}")


def _threshold(high_val: int, low_val: int, slider: int) -> int:
    """Linear interpolation: slider 1 -> high_val, slider 10 -> low_val."""
    return int(high_val - (high_val - low_val) * (slider - 1) / 9)


def generate_preset(
    style: str,
    aggression: int = 5,
    risk_tolerance: int = 5,
) -> str:
    """Generate decide() function body source code for a playstyle preset.

    Args:
        style: One of PRESET_NAMES
        aggression: 1-10, higher = more aggressive behavior
        risk_tolerance: 1-10, higher = takes more risks

    Returns:
        Python source code string for a complete decide() function body
        (NOT including the ``def decide(state):`` line).

    Raises:
        ValueError: If style is unknown or sliders are out of range.
    """
    if style not in PRESET_NAMES:
        raise ValueError(
            f"style must be one of {PRESET_NAMES!r}, got {style!r}"
        )
    _validate_slider("aggression", aggression)
    _validate_slider("risk_tolerance", risk_tolerance)

    body_lines = _BUILDERS[style](aggression, risk_tolerance)
    return "\n".join(_PREAMBLE + body_lines)


# --- individual preset builders ---


def _build_aggro(aggression: int, risk: int) -> list[str]:
    rest_hp = _threshold(40, 10, risk)
    chase_range = _threshold(3, 8, aggression)
    min_energy = _threshold(20, 5, risk)
    return [
        f"if me.hp < {rest_hp} or me.energy < {min_energy}:",
        "    return me.rest()",
        "target = enemies.weakest()",
        "if target and me.dist_to(target) == 1:",
        "    return me.attack(target)",
        f"if target and me.dist_to(target) <= {chase_range}:",
        "    return me.move_toward(target)",
        "return me.move_toward_center()",
    ]


def _build_tank(aggression: int, risk: int) -> list[str]:
    defend_hp = _threshold(70, 30, risk)
    counter_hp = _threshold(60, 30, aggression)
    rest_energy = _threshold(40, 15, risk)
    return [
        f"if me.energy < {rest_energy}:",
        "    return me.rest()",
        "adj = enemies.adjacent()",
        f"if adj and me.hp >= {counter_hp}:",
        "    return me.attack(adj[0])",
        f"if me.hp < {defend_hp}:",
        "    return me.defend()",
        "if adj:",
        "    return me.defend()",
        "return me.move_toward_center()",
    ]


def _build_kiter(aggression: int, risk: int) -> list[str]:
    safe_range = _threshold(4, 2, aggression)
    flee_hp = _threshold(60, 20, risk)
    attack_wounded = _threshold(60, 30, aggression)
    return [
        f"if me.hp < {flee_hp}:",
        "    nearest = enemies.closest()",
        "    if nearest:",
        "        return me.move_away_from(nearest)",
        "    return me.rest()",
        f"wounded = enemies.wounded({attack_wounded})",
        "if wounded and me.dist_to(wounded[0]) == 1:",
        "    return me.attack(wounded[0])",
        "nearest = enemies.closest()",
        f"if nearest and me.dist_to(nearest) < {safe_range}:",
        "    return me.move_away_from(nearest)",
        f"if nearest and me.dist_to(nearest) > {safe_range + 1}:",
        "    return me.move_toward(nearest)",
        "return me.rest()",
    ]


def _build_opportunist(aggression: int, risk: int) -> list[str]:
    rest_energy = _threshold(40, 15, risk)
    wound_threshold = _threshold(70, 30, aggression)
    engage_hp = _threshold(50, 20, risk)
    return [
        f"if me.energy < {rest_energy}:",
        "    return me.rest()",
        f"wounded = enemies.wounded({wound_threshold})",
        f"if wounded and me.hp >= {engage_hp} and me.dist_to(wounded[0]) == 1:",
        "    return me.attack(wounded[0])",
        f"if wounded and me.hp >= {engage_hp}:",
        "    return me.move_toward(wounded[0])",
        "adj = enemies.adjacent()",
        "if adj:",
        "    return me.defend()",
        "return me.rest()",
    ]


def _build_chaos(aggression: int, risk: int) -> list[str]:
    attack_weight = _threshold(1, 5, aggression)
    rest_weight = _threshold(4, 1, risk)
    return [
        "import random",
        "target = enemies.closest()",
        (
            f"actions = [('attack', {attack_weight}), ('defend', 2), "
            f"('move', 2), ('rest', {rest_weight})]"
        ),
        "choices, weights = zip(*actions)",
        "pick = random.choices(choices, weights=weights, k=1)[0]",
        "if pick == 'attack' and target and me.dist_to(target) == 1:",
        "    return me.attack(target)",
        "if pick == 'attack' and target:",
        "    return me.move_toward(target)",
        "if pick == 'defend':",
        "    return me.defend()",
        "if pick == 'move':",
        "    return me.move_toward_center()",
        "return me.rest()",
    ]


_BUILDERS: dict[str, Callable[[int, int], list[str]]] = {
    "aggro": _build_aggro,
    "tank": _build_tank,
    "kiter": _build_kiter,
    "opportunist": _build_opportunist,
    "chaos": _build_chaos,
}
