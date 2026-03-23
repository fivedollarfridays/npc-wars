"""Character descriptor -- maps stats + equipment to visual identity."""

from __future__ import annotations

from typing import Any

from engine.archetype import classify_archetype
from engine.stats import DEFAULT_ALLOCATION, StatAllocation

__all__ = ["build_character_descriptor", "classify_archetype"]

SHAPE_MAP: dict[str, str] = {
    "Balanced": "circle",
    "Tank": "square",
    "Assassin": "triangle",
    "Bruiser": "hexagon",
    "Controller": "diamond",
}

COLOR_MAP: dict[str, str] = {
    "Balanced": "#e0e0f0",
    "Tank": "#4488ff",
    "Assassin": "#aa44ff",
    "Bruiser": "#ff4444",
    "Controller": "#44ff88",
}

WEAPON_INDICATOR: dict[str, str] = {
    "dagger": "dot",
    "sword": "line",
    "spear": "long_line",
    "axe": "wedge",
    "bow": "arc",
    "mace": "circle",
}

ARMOR_BORDER: dict[str, int] = {
    "leather": 1,
    "chain_mail": 2,
    "reinforced": 2,
    "plate": 3,
    "crystal": 1,
}


def build_character_descriptor(
    stats: StatAllocation | None = None,
    equipment: dict[str, Any] | None = None,
    archetype: str | None = None,
) -> dict[str, Any]:
    """Build visual descriptor from stats + equipment.

    Returns a dict consumed by the viewer for rendering shape,
    color, weapon indicator, border thickness, and size.
    """
    if stats is None:
        stats = DEFAULT_ALLOCATION
    if archetype is None:
        archetype = classify_archetype(stats)

    weapon = (equipment or {}).get("weapon", "sword")
    armor = (equipment or {}).get("armor", "leather")

    return {
        "shape": SHAPE_MAP.get(archetype, "circle"),
        "color": COLOR_MAP.get(archetype, "#e0e0f0"),
        "archetype": archetype,
        "border_thickness": ARMOR_BORDER.get(armor, 1),
        "weapon_indicator": WEAPON_INDICATOR.get(weapon, "line"),
        "size_scale": 14 + (stats.armor - 25) * 0.15,
        "weapon": weapon,
        "armor": armor,
    }
