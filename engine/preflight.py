"""Preflight execution check -- verify decide() runs before accepting a bot."""

from __future__ import annotations

import os
import tempfile
from typing import Any

from engine.bot_scanner import load_bot_module
from engine.combat import DEFAULT_UNLOCKED_ACTIONS

__all__ = ["run_preflight", "build_sample_state"]


def _build_sample_me() -> dict[str, Any]:
    """Build the 'me' dict for sample state."""
    return {
        "x": 5, "y": 5, "hp": 145.0, "energy": 100,
        "attack_power": 25, "defense": 0, "score": 0,
        "momentum_tier": 0, "momentum_name": "",
        "is_leader": False,
        "power": 25, "speed": 25, "armor": 25, "mind": 25,
        "max_hp": 145, "max_energy": 100,
        "min_damage": 35, "max_damage": 55,
        "dodge_chance": 7.5, "damage_reduction": 0.0,
        "unlocked_actions": sorted(DEFAULT_UNLOCKED_ACTIONS),
        "line_budget": 50, "win_streak": 0,
        "passive_rounds": 0,
        "traps": [], "trap_cooldown": 0,
        "tactical_cooldown": 0,
        "callbacks": [],
        "equipment": {
            "weapon": "sword", "armor": "leather",
            "accessories": [], "tactical": None,
        },
        "equipment_bonuses": {
            "to_hit": 1, "min_damage": 3, "max_damage": 5, "dr": 2,
            "max_hp": 0, "max_energy": 0, "dodge": 0, "crit_mult": 0,
            "initiative": 0, "armor_pierce": 0, "special_weapon": "versatile",
        },
        "ability": None,
        "on_terrain": "open",
        "terrain": {
            "map": "arena", "walls": [], "water": [],
            "high_ground": [], "cover": [], "crystals": [],
        },
        "hit_chance_vs": {},
        "incoming_threat": [],
        "glyph": "○",
    }


def _build_sample_enemy() -> dict[str, Any]:
    """Build a single enemy dict for sample state."""
    return {
        "x": 7, "y": 3, "hp": 100.0, "emoji": "E", "name": "Enemy",
        "glyph": "●", "score": 0, "momentum_tier": 0, "is_leader": False,
        "max_hp": 145, "speed_class": "normal",
        "has_traps": False, "trap_count": 0,
        "weapon": "sword", "armor": "leather",
        "has_ability": False, "on_terrain": "open",
    }


def build_sample_state(grid_size: int = 10) -> dict[str, Any]:
    """Build a minimal valid state dict for preflight testing."""
    return {
        "me": _build_sample_me(),
        "enemies": [_build_sample_enemy()],
        "grid_size": grid_size,
        "storm_border": 0,
        "round": 5,
        "bumps_last_round": [],
    }


def _load_module_from_source(source: str) -> Any:
    """Write source to a temp file, load via bot_scanner, clean up."""
    with tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", delete=False,
    ) as f:
        f.write(source)
        f.flush()
        tmp_path = f.name
    try:
        return load_bot_module(tmp_path)
    finally:
        os.unlink(tmp_path)


def run_preflight(
    source: str,
    unlocked_actions: set[str] | None = None,
) -> tuple[bool, str]:
    """Run preflight check on bot source code.

    Returns (True, "OK") if bot passes, (False, "error message") if it fails.
    """
    if unlocked_actions is None:
        unlocked_actions = set(DEFAULT_UNLOCKED_ACTIONS)

    # Step 1: Load module (includes AST security scan)
    try:
        module = _load_module_from_source(source)
    except ValueError as e:
        return False, f"Security scan failed: {e}"
    except Exception as e:
        return False, f"Failed to load bot module: {e}"

    # Step 2: Check decide function exists
    decide = getattr(module, "decide", None)
    if decide is None or not callable(decide):
        return False, "Bot has no callable decide() function"

    # Step 3: Run decide with sample state
    state = build_sample_state()
    try:
        action = decide(state)
    except Exception as e:
        return False, f"decide() crashed: {type(e).__name__}: {e}"

    # Step 4: Validate returned action
    if action is None:
        return False, "decide() returned None"
    if not isinstance(action, tuple) or len(action) == 0:
        return False, (
            f"decide() returned invalid type: {type(action).__name__} "
            f"(expected tuple)"
        )

    action_name = action[0]
    if action_name not in unlocked_actions and action_name not in ("rest", "nothing"):
        return False, (
            f"decide() returned action '{action_name}' which is not in "
            f"unlocked actions: {sorted(unlocked_actions)}"
        )

    return True, "OK"
