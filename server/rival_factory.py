"""Rival agent factory -- generates tier-specific training opponents.

Each rival uses a preset strategy as its base with custom override lines
injected after the storm check. If the override triggers, it returns early;
otherwise the preset's fallback logic handles the decision.
"""

from __future__ import annotations

import textwrap
from typing import Any

from agentgrounds.wars.presets import generate_preset

__all__ = ["RIVAL_EMOJI", "MAX_TIER", "generate_rival"]

RIVAL_EMOJI = "\U0001f3af"  # target emoji
MAX_TIER = 5

# --- Tier definitions --------------------------------------------------------

RIVAL_TIERS: dict[int, dict[str, Any]] = {
    1: {
        "name": "The Bully",
        "bio": "Rival Tier 1: Punishes passive play",
        "base_style": "aggro",
        "aggression": 9,
        "risk_tolerance": 8,
        "override_lines": [
            "# RIVAL: Always attack adjacent enemies (punish passivity)",
            "adj = enemies.adjacent()",
            "if adj:",
            "    target = min(adj, key=lambda e: e['hp'])",
            "    return me.attack(target)",
        ],
    },
    2: {
        "name": "The Storm Chaser",
        "bio": "Rival Tier 2: Exploits poor positioning",
        "base_style": "kiter",
        "aggression": 6,
        "risk_tolerance": 7,
        "override_lines": [
            "# RIVAL: Reposition toward center in late game",
            "if storm.danger is False and (state['round'] >= 8 or state['storm_border'] > 0):",
            "    cx = me.grid_size // 2",
            "    my_dist = abs(me.x - cx) + abs(me.y - cx)",
            "    if my_dist > 3:",
            "        return me.move_toward_center()",
        ],
    },
    3: {
        "name": "The Economist",
        "bio": "Rival Tier 3: Punishes energy waste",
        "base_style": "opportunist",
        "aggression": 7,
        "risk_tolerance": 5,
        "override_lines": [
            "# RIVAL: Energy-efficient — rest to build reserves, strike when flush",
            "if me.energy < 30:",
            "    adj = enemies.adjacent()",
            "    if adj:",
            "        return me.defend()",
            "    return me.rest()",
            "if me.energy >= 60:",
            "    adj = enemies.adjacent()",
            "    if adj:",
            "        target = min(adj, key=lambda e: e['hp'])",
            "        return me.attack(target)",
            "nearest = enemies.closest()",
            "if nearest and me.dist_to(nearest) > 2 and me.energy < 60:",
            "    return me.rest()",
        ],
    },
    4: {
        "name": "The Counter",
        "bio": "Rival Tier 4: Learns your patterns, counters them",
        "base_style": "tank",
        "aggression": 7,
        "risk_tolerance": 4,
        "override_lines": [
            "# RIVAL: Defensive counter-play (fallback when no pattern data)",
            "adj = enemies.adjacent()",
            "if adj and me.hp > 50:",
            "    return me.defend()",
            "if adj and me.hp <= 50:",
            "    target = min(adj, key=lambda e: e['hp'])",
            "    return me.attack(target)",
        ],
    },
    5: {
        "name": "The Mirror",
        "bio": "Rival Tier 5: Adapts to your exact strategy",
        "base_style": "aggro",
        "aggression": 10,
        "risk_tolerance": 5,
        "override_lines": [
            "# RIVAL: Fallback — low HP flee, else crush weakest",
            "if me.hp < 30:",
            "    nearest = enemies.closest()",
            "    if nearest:",
            "        return me.move_away_from(nearest)",
            "    return me.rest()",
            "adj = enemies.adjacent()",
            "if adj:",
            "    target = min(adj, key=lambda e: e['hp'])",
            "    return me.attack(target)",
            "target = enemies.weakest()",
            "if target:",
            "    return me.move_toward(target)",
        ],
    },
}


def generate_rival(
    tier: int,
    *,
    pattern_data: dict[str, dict[str, float]] | None = None,
    accuracy_cap: float | None = None,
) -> dict[str, Any]:
    """Generate a rival bot config for the given tier.

    Args:
        tier: Rival tier (1-5).
        pattern_data: Optional {context: {action: probability}} for Tier 4/5.
            Embedded as a dict literal in generated source.
        accuracy_cap: Optional accuracy cap for Tier 5 Mirror (0.0-1.0).

    Returns a dict compatible with run_match() bot configs:
    name, emoji, bio, decide_func, source, is_rival, rival_tier.
    """
    if tier not in RIVAL_TIERS:
        raise ValueError(
            f"Invalid rival tier: {tier}. Valid: {sorted(RIVAL_TIERS)}"
        )

    cfg = RIVAL_TIERS[tier]
    preset_body = generate_preset(
        cfg["base_style"], cfg["aggression"], cfg["risk_tolerance"],
    )

    if tier == 5 and pattern_data and accuracy_cap is not None:
        source = _build_mirror_source(tier, cfg, preset_body, pattern_data, accuracy_cap)
    elif tier == 4 and pattern_data:
        source = _build_counter_source(tier, cfg, preset_body, pattern_data)
    else:
        source = _build_rival_source(tier, cfg, preset_body)

    return _compile_rival_source(source, cfg, tier)


def _compile_rival_source(
    source: str, cfg: dict[str, Any], tier: int,
) -> dict[str, Any]:
    """Compile rival source and return a bot config dict."""
    namespace: dict[str, Any] = {}
    exec(compile(source, f"<rival_tier_{tier}>", "exec"), namespace)  # noqa: S102
    return {
        "name": cfg["name"],
        "emoji": RIVAL_EMOJI,
        "bio": cfg["bio"],
        "decide_func": namespace["decide"],
        "source": source,
        "is_rival": True,
        "rival_tier": tier,
    }


_COUNTER_MAP: dict[str, str] = {
    "attack": "defend",
    "rest": "attack",
    "defend": "attack",
    "move": "attack",
    "ranged_attack": "move",
    "dash": "defend",
}


def _counter_override_lines(
    pattern_data: dict[str, dict[str, float]],
) -> list[str]:
    """Generate inline counter logic lines for embedding in decide() body."""
    return [
        "",
        f"_pd = {repr(pattern_data)}",
        f"_cm = {repr(_COUNTER_MAP)}",
        "# RIVAL: Pattern-based counter (learned from your matches)",
        "_ctxs = []",
        "if enemies.adjacent():",
        "    _ctxs.append('at_range_1')",
        "if me.hp < 30:",
        "    _ctxs.append('below_30_hp')",
        "for _ctx in _ctxs:",
        "    if _ctx in _pd and _pd[_ctx]:",
        "        _predicted = max(_pd[_ctx], key=_pd[_ctx].get)",
        "        _counter = _cm.get(_predicted, 'defend')",
        "        if _counter == 'defend':",
        "            return me.defend()",
        "        if _counter == 'attack':",
        "            _adj = enemies.adjacent()",
        "            if _adj:",
        "                return me.attack(min(_adj, key=lambda e: e['hp']))",
        "        if _counter == 'move':",
        "            _near = enemies.closest()",
        "            if _near:",
        "                return me.move_toward(_near)",
        "        break",
        "",
    ]


def _build_counter_source(
    tier: int,
    cfg: dict[str, Any],
    preset_body: str,
    pattern_data: dict[str, dict[str, float]],
) -> str:
    """Build source with embedded pattern data for The Counter."""
    lines = preset_body.split("\n")
    inject_idx = _find_injection_point(lines)

    counter_lines = _counter_override_lines(pattern_data)
    fallback = cfg["override_lines"]
    combined = (
        lines[:inject_idx] + counter_lines + [""] + fallback + [""]
        + lines[inject_idx:]
    )
    body = "\n".join(combined)

    return (
        f'BOT_NAME = "Rival T{tier}: {cfg["name"]}"\n'
        f'BOT_EMOJI = "{RIVAL_EMOJI}"\n'
        f'BOT_BIO = "{cfg["bio"]}"\n'
        f"\n"
        f"def decide(state):\n"
        f"{textwrap.indent(body, '    ')}\n"
    )


def _mirror_override_lines(
    pattern_data: dict[str, dict[str, float]],
    accuracy_cap: float,
) -> list[str]:
    """Generate inline mirror logic: multi-context prediction + accuracy gate."""
    return [
        "",
        "import random as _rng",
        f"_pd = {repr(pattern_data)}",
        f"_cm = {repr(_COUNTER_MAP)}",
        f"_accuracy_cap = {accuracy_cap!r}",
        "# RIVAL: Mirror — adaptive pattern counter with accuracy cap",
        "_best_pred = None",
        "_best_conf = 0.0",
        "_ctxs = []",
        "if enemies.adjacent():",
        "    _ctxs.append('at_range_1')",
        "if me.hp < 30:",
        "    _ctxs.append('below_30_hp')",
        "for _ctx in _ctxs:",
        "    if _ctx in _pd and _pd[_ctx]:",
        "        _top = max(_pd[_ctx], key=_pd[_ctx].get)",
        "        if _pd[_ctx][_top] > _best_conf:",
        "            _best_conf = _pd[_ctx][_top]",
        "            _best_pred = _top",
        "if _best_pred is not None:",
        "    if _rng.random() > _accuracy_cap:",
        "        _pick = _rng.choice(['attack', 'defend', 'rest', 'move'])",
        "    else:",
        "        _pick = _cm.get(_best_pred, 'defend')",
        "    if _pick == 'defend':",
        "        return me.defend()",
        "    if _pick == 'attack':",
        "        _adj = enemies.adjacent()",
        "        if _adj:",
        "            return me.attack(min(_adj, key=lambda e: e['hp']))",
        "    if _pick == 'rest':",
        "        return me.rest()",
        "    if _pick == 'move':",
        "        _near = enemies.closest()",
        "        if _near:",
        "            return me.move_toward(_near)",
        "",
    ]


def _build_mirror_source(
    tier: int,
    cfg: dict[str, Any],
    preset_body: str,
    pattern_data: dict[str, dict[str, float]],
    accuracy_cap: float,
) -> str:
    """Build source with embedded pattern data + accuracy cap for The Mirror."""
    lines = preset_body.split("\n")
    inject_idx = _find_injection_point(lines)

    mirror_lines = _mirror_override_lines(pattern_data, accuracy_cap)
    fallback = cfg["override_lines"]
    combined = (
        lines[:inject_idx] + mirror_lines + [""] + fallback + [""]
        + lines[inject_idx:]
    )
    body = "\n".join(combined)

    return (
        f'BOT_NAME = "Rival T{tier}: {cfg["name"]}"\n'
        f'BOT_EMOJI = "{RIVAL_EMOJI}"\n'
        f'BOT_BIO = "{cfg["bio"]}"\n'
        f"\n"
        f"def decide(state):\n"
        f"{textwrap.indent(body, '    ')}\n"
    )


def _build_rival_source(
    tier: int,
    cfg: dict[str, Any],
    preset_body: str,
) -> str:
    """Build the full source with overrides injected after storm check."""
    lines = preset_body.split("\n")
    inject_idx = _find_injection_point(lines)

    override_block = [""] + cfg["override_lines"] + [""]
    combined = lines[:inject_idx] + override_block + lines[inject_idx:]
    body = "\n".join(combined)

    return (
        f'BOT_NAME = "Rival T{tier}: {cfg["name"]}"\n'
        f'BOT_EMOJI = "{RIVAL_EMOJI}"\n'
        f'BOT_BIO = "{cfg["bio"]}"\n'
        f"\n"
        f"def decide(state):\n"
        f"{textwrap.indent(body, '    ')}\n"
    )


def _find_injection_point(lines: list[str]) -> int:
    """Find the line index after the storm-flee block in preset body."""
    for i, line in enumerate(lines):
        if "flee_storm" in line:
            return i + 1
    # Fallback: after the Storm(state) setup line
    for i, line in enumerate(lines):
        if "Storm(state)" in line:
            return i + 1
    return 0
