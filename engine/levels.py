"""Level progression table and calculator — pure data + pure functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Hand-authored milestone levels ──────────────────────────────────

_MILESTONES: list[dict[str, Any]] = [
    {"level": 1, "xp_required": 0, "line_budget": 50,
     "new_actions": ["move", "attack", "rest", "defend"],
     "new_callbacks": ["decide"], "milestone": "Starting out"},
    {"level": 2, "xp_required": 100, "line_budget": 60,
     "new_actions": [], "new_callbacks": [], "milestone": ""},
    {"level": 3, "xp_required": 250, "line_budget": 75,
     "new_actions": ["ranged_attack"], "new_callbacks": [],
     "milestone": "First new action"},
    {"level": 5, "xp_required": 600, "line_budget": 100,
     "new_actions": ["dash"], "new_callbacks": ["on_kill"],
     "milestone": "Mobility unlock"},
    {"level": 8, "xp_required": 1200, "line_budget": 125,
     "new_actions": ["taunt"], "new_callbacks": ["setup"],
     "milestone": "Pre-match config"},
    {"level": 10, "xp_required": 1800, "line_budget": 140,
     "new_actions": [], "new_callbacks": [], "milestone": "Veteran"},
    {"level": 12, "xp_required": 2800, "line_budget": 150,
     "new_actions": ["trap"], "new_callbacks": ["react"],
     "milestone": "Reactive play"},
    {"level": 15, "xp_required": 4500, "line_budget": 175,
     "new_actions": [], "new_callbacks": [], "milestone": ""},
    {"level": 18, "xp_required": 7000, "line_budget": 200,
     "new_actions": ["use_ability"], "new_callbacks": ["power_up"],
     "milestone": "Custom ability 1"},
    {"level": 22, "xp_required": 11000, "line_budget": 225,
     "new_actions": [], "new_callbacks": ["evolve"],
     "milestone": "Adaptation"},
    {"level": 25, "xp_required": 15000, "line_budget": 250,
     "new_actions": [], "new_callbacks": ["power_up"],
     "milestone": "Custom ability 2"},
    {"level": 30, "xp_required": 25000, "line_budget": 300,
     "new_actions": [], "new_callbacks": [], "milestone": "Master tier"},
]


def _build_level_table() -> dict[int, dict[str, Any]]:
    """Build the full 1-30 level table, interpolating gaps."""
    table: dict[int, dict[str, Any]] = {}
    for m in _MILESTONES:
        table[m["level"]] = {
            "xp_required": m["xp_required"],
            "line_budget": m["line_budget"],
            "new_actions": list(m["new_actions"]),
            "new_callbacks": list(m["new_callbacks"]),
            "milestone": m["milestone"],
        }

    # Sort milestone levels for interpolation
    defined = sorted(table.keys())

    for lvl in range(1, 31):
        if lvl in table:
            continue
        # Find surrounding defined levels
        lo = max(d for d in defined if d < lvl)
        hi = min(d for d in defined if d > lvl)
        frac = (lvl - lo) / (hi - lo)
        xp = int(table[lo]["xp_required"]
                 + frac * (table[hi]["xp_required"] - table[lo]["xp_required"]))
        budget = int(table[lo]["line_budget"]
                     + frac * (table[hi]["line_budget"] - table[lo]["line_budget"]))
        table[lvl] = {
            "xp_required": xp,
            "line_budget": budget,
            "new_actions": [],
            "new_callbacks": [],
            "milestone": "",
        }

    return dict(sorted(table.items()))


LEVEL_TABLE: dict[int, dict[str, Any]] = _build_level_table()

MAX_LEVEL = 30


def level_from_xp(total_xp: int) -> int:
    """Return the highest level where xp_required <= total_xp."""
    result = 1
    for lvl in range(1, MAX_LEVEL + 1):
        if LEVEL_TABLE[lvl]["xp_required"] <= total_xp:
            result = lvl
    return result


def xp_for_next_level(current_level: int) -> int:
    """Total XP needed for the next level. At max, returns max XP."""
    if current_level >= MAX_LEVEL:
        return LEVEL_TABLE[MAX_LEVEL]["xp_required"]
    return LEVEL_TABLE[current_level + 1]["xp_required"]


def xp_to_next_level(current_level: int, current_xp: int) -> int:
    """XP remaining to reach the next level. 0 at max level."""
    if current_level >= MAX_LEVEL:
        return 0
    return max(0, xp_for_next_level(current_level) - current_xp)


@dataclass(frozen=True)
class LevelUnlocks:
    """Cumulative unlocks available at a given level."""

    actions: set[str] = field(default_factory=set)
    callbacks: set[str] = field(default_factory=set)
    line_budget: int = 50


def unlocks_at_level(level: int) -> LevelUnlocks:
    """Return cumulative unlocks up to and including *level*."""
    actions: set[str] = set()
    callbacks: set[str] = set()
    budget = 50
    for lvl in range(1, min(level, MAX_LEVEL) + 1):
        entry = LEVEL_TABLE[lvl]
        actions.update(entry["new_actions"])
        callbacks.update(entry["new_callbacks"])
        budget = entry["line_budget"]
    return LevelUnlocks(actions=actions, callbacks=callbacks, line_budget=budget)
