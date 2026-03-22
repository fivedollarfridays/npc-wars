"""Archetype classification from stat allocations.

Pure function — no I/O, no side effects.
"""

from __future__ import annotations

from engine.stats import StatAllocation

__all__ = ["ARCHETYPE_NAMES", "classify_archetype"]

# Mapping: stat field name -> archetype display name
ARCHETYPE_NAMES: dict[str, str] = {
    "power": "Bruiser",
    "speed": "Assassin",
    "armor": "Tank",
    "mind": "Controller",
    "balanced": "Balanced",
}

_DOMINANT_THRESHOLD = 35
_BALANCED_LOW = 20
_BALANCED_HIGH = 30


def classify_archetype(stats: StatAllocation) -> str:
    """Classify a bot's archetype from its stat allocation.

    Rules:
    - If one stat > 35 -> named after that stat
    - If all stats 20-30 -> "Balanced"
    - Otherwise -> name by highest stat
    """
    stat_map = {
        "power": stats.power,
        "speed": stats.speed,
        "armor": stats.armor,
        "mind": stats.mind,
    }

    # Check for dominant stat (> 35)
    for name, value in stat_map.items():
        if value > _DOMINANT_THRESHOLD:
            return ARCHETYPE_NAMES[name]

    # Check for balanced (all 20-30)
    if all(_BALANCED_LOW <= v <= _BALANCED_HIGH for v in stat_map.values()):
        return ARCHETYPE_NAMES["balanced"]

    # Fallback: name by highest stat
    highest = max(stat_map, key=lambda k: stat_map[k])
    return ARCHETYPE_NAMES[highest]
