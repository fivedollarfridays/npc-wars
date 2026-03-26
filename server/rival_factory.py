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
        "name": "The Executioner",
        "bio": "Rival Tier 3: Finishes wounded targets ruthlessly",
        "base_style": "opportunist",
        "aggression": 8,
        "risk_tolerance": 6,
        "override_lines": [
            "# RIVAL: Chase and finish any wounded enemy",
            "wounded = enemies.wounded(50)",
            "if wounded:",
            "    target = min(wounded, key=lambda e: e['hp'])",
            "    if me.dist_to(target) == 1:",
            "        return me.attack(target)",
            "    return me.move_toward(target)",
        ],
    },
    4: {
        "name": "The Fortress",
        "bio": "Rival Tier 4: Impenetrable defense with counter-attacks",
        "base_style": "tank",
        "aggression": 7,
        "risk_tolerance": 4,
        "override_lines": [
            "# RIVAL: Defend when outnumbered, counter weak adjacent",
            "adj = enemies.adjacent()",
            "if len(adj) > 1:",
            "    return me.defend()",
            "if adj and adj[0]['hp'] < me.hp:",
            "    return me.attack(adj[0])",
        ],
    },
    5: {
        "name": "The Grandmaster",
        "bio": "Rival Tier 5: Adapts to any situation",
        "base_style": "aggro",
        "aggression": 10,
        "risk_tolerance": 5,
        "override_lines": [
            "# RIVAL: Adaptive — low HP flee, else crush weakest",
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


def generate_rival(tier: int) -> dict[str, Any]:
    """Generate a rival bot config for the given tier.

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
    source = _build_rival_source(tier, cfg, preset_body)

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
