"""Equipment catalog, budget validation, and bonus computation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "EQUIPMENT_BUDGET",
    "EQUIPMENT_CATALOG",
    "EQUIPMENT_DEFAULTS",
    "EquipmentBonuses",
    "compute_equipment_bonuses",
    "validate_equipment",
]

EQUIPMENT_BUDGET = 40

# ── Catalog ─────────────────────────────────────────────────────────

EQUIPMENT_CATALOG: dict[str, dict[str, dict[str, Any]]] = {
    "weapon": {
        "dagger": {
            "cost": 5, "to_hit": 2, "min_dmg": 2, "max_dmg": 2,
            "special": "finesse",
        },
        "sword": {
            "cost": 8, "to_hit": 1, "min_dmg": 3, "max_dmg": 5,
            "special": "versatile",
        },
        "axe": {
            "cost": 9, "to_hit": -1, "min_dmg": 1, "max_dmg": 10,
            "special": "high_variance", "crit_mult_bonus": 0.2,
        },
        "mace": {
            "cost": 7, "to_hit": 0, "min_dmg": 4, "max_dmg": 4,
            "special": "armor_piercing", "armor_pierce": 4,
        },
        "bow": {
            "cost": 6, "to_hit": 1, "min_dmg": 1, "max_dmg": 3,
            "special": "ranged_preferred",
        },
        "spear": {
            "cost": 8, "to_hit": 0, "min_dmg": 2, "max_dmg": 6,
            "special": "reach", "reach_distance": 2,
        },
    },
    "armor": {
        "leather": {"cost": 6, "dr_bonus": 2, "energy_penalties": {}},
        "chain_mail": {
            "cost": 8, "dr_bonus": 4,
            "energy_penalties": {
                "move": 2, "attack": 2, "defend": 2,
                "dash": 2, "ranged_attack": 2, "trap": 2,
            },
        },
        "plate": {
            "cost": 11, "dr_bonus": 6,
            "energy_penalties": {"move": 4, "dash": 4, "ranged_attack": 4},
        },
        "reinforced": {
            "cost": 10, "dr_bonus": 3,
            "energy_penalties": {
                "move": 1, "attack": 1, "defend": 1,
                "dash": 1, "ranged_attack": 1, "trap": 1,
            },
        },
        "crystal": {
            "cost": 14, "dr_bonus": 1, "energy_penalties": {},
            "rest_energy_bonus": 1,
        },
    },
    "accessory": {
        "ring_of_health": {"cost": 4, "max_hp_bonus": 10},
        "ring_of_haste": {
            "cost": 5, "initiative_bonus": 2, "energy_cost_reduction": 1,
        },
        "amulet_of_crit": {
            "cost": 6, "crit_mult_bonus": 0.3, "crit_chance_bonus": 5.0,
        },
        "charm_of_evasion": {"cost": 5, "dodge_bonus": 3.0},
        "pendant_of_mind": {
            "cost": 4, "max_energy_bonus": 10, "energy_regen_bonus": 2,
        },
        "cloak_of_shadows": {"cost": 7, "dr_bonus": 3},
        "boots_of_speed": {"cost": 6, "initiative_bonus": 5},
        "compass": {"cost": 3, "to_hit_bonus": 1},
    },
    "tactical": {
        "battle_cry": {
            "cost": 8, "type": "activated",
            "damage_mult": 1.5, "energy_cost": 15, "cooldown": 4,
        },
        "fortify": {
            "cost": 10, "type": "activated",
            "dr_bonus_temp": 6, "hp_bonus_temp": 10,
            "energy_cost": 12, "cooldown": 5,
        },
        "teleport": {
            "cost": 14, "type": "activated",
            "distance": 3, "energy_cost": 20, "cooldown": 3,
        },
        "overdrive": {
            "cost": 16, "type": "passive",
            "damage_bonus": 2, "attack_energy_increase": 3,
        },
    },
}

EQUIPMENT_DEFAULTS: dict[str, Any] = {
    "weapon": "sword",
    "armor": "leather",
    "accessories": [],
    "tactical": None,
}


# ── Validation ──────────────────────────────────────────────────────


def validate_equipment(selections: dict[str, Any]) -> tuple[bool, str]:
    """Validate an equipment loadout against catalog and budget.

    *selections* keys: weapon (str), armor (str),
    accessories (list[str]), tactical (str | None).
    Returns (True, "Valid: X/40 credits") or (False, reason).
    """
    # Weapon
    weapon = selections.get("weapon")
    if not weapon or weapon not in EQUIPMENT_CATALOG["weapon"]:
        return False, f"Invalid or missing weapon: {weapon}"

    # Armor
    armor = selections.get("armor")
    if not armor or armor not in EQUIPMENT_CATALOG["armor"]:
        return False, f"Invalid or missing armor: {armor}"

    # Accessories
    accessories: list[str] = selections.get("accessories", [])
    if not isinstance(accessories, list):
        return False, "accessories must be a list"
    if len(accessories) > 2:
        return False, f"Max 2 accessories, got {len(accessories)}"
    for acc in accessories:
        if acc not in EQUIPMENT_CATALOG["accessory"]:
            return False, f"Unknown accessory: {acc}"

    # Tactical
    tactical = selections.get("tactical")
    if tactical is not None and tactical not in EQUIPMENT_CATALOG["tactical"]:
        return False, f"Unknown tactical: {tactical}"

    # Budget
    total = _total_cost(weapon, armor, accessories, tactical)
    if total > EQUIPMENT_BUDGET:
        return False, f"Over budget: {total}/{EQUIPMENT_BUDGET} credits"

    return True, f"Valid: {total}/{EQUIPMENT_BUDGET} credits"


def _total_cost(
    weapon: str, armor: str, accessories: list[str], tactical: str | None,
) -> int:
    cost = EQUIPMENT_CATALOG["weapon"][weapon]["cost"]
    cost += EQUIPMENT_CATALOG["armor"][armor]["cost"]
    cost += sum(EQUIPMENT_CATALOG["accessory"][a]["cost"] for a in accessories)
    if tactical:
        cost += EQUIPMENT_CATALOG["tactical"][tactical]["cost"]
    return int(cost)


# ── Bonus aggregation ───────────────────────────────────────────────


@dataclass
class EquipmentBonuses:
    """Aggregated bonuses from a complete equipment loadout."""

    to_hit: int = 0
    min_damage: int = 0
    max_damage: int = 0
    dr: int = 0
    max_hp: int = 0
    max_energy: int = 0
    dodge: float = 0.0
    crit_mult: float = 0.0
    crit_chance: float = 0.0
    initiative: int = 0
    energy_regen: int = 0
    action_cost_mods: dict[str, int] = field(default_factory=dict)
    rest_energy_bonus: int = 0
    armor_pierce: int = 0
    special_weapon: str = ""
    reach_distance: int = 0


def compute_equipment_bonuses(selections: dict[str, Any]) -> EquipmentBonuses:
    """Aggregate bonuses from all selected equipment items."""
    b = EquipmentBonuses()
    weapon = selections.get("weapon", "")
    if weapon and weapon in EQUIPMENT_CATALOG["weapon"]:
        _apply_weapon(b, EQUIPMENT_CATALOG["weapon"][weapon])

    armor = selections.get("armor", "")
    if armor and armor in EQUIPMENT_CATALOG["armor"]:
        _apply_armor(b, EQUIPMENT_CATALOG["armor"][armor])

    for acc in selections.get("accessories", []):
        if acc in EQUIPMENT_CATALOG["accessory"]:
            _apply_accessory(b, EQUIPMENT_CATALOG["accessory"][acc])

    return b


def _apply_weapon(b: EquipmentBonuses, w: dict[str, Any]) -> None:
    b.to_hit += w.get("to_hit", 0)
    b.min_damage += w.get("min_dmg", 0)
    b.max_damage += w.get("max_dmg", 0)
    b.crit_mult += w.get("crit_mult_bonus", 0.0)
    b.armor_pierce += w.get("armor_pierce", 0)
    b.reach_distance = max(b.reach_distance, w.get("reach_distance", 0))
    b.special_weapon = w.get("special", "")


def _apply_armor(b: EquipmentBonuses, a: dict[str, Any]) -> None:
    b.dr += a.get("dr_bonus", 0)
    b.rest_energy_bonus += a.get("rest_energy_bonus", 0)
    for action, penalty in a.get("energy_penalties", {}).items():
        b.action_cost_mods[action] = b.action_cost_mods.get(action, 0) + penalty


def _apply_accessory(b: EquipmentBonuses, acc: dict[str, Any]) -> None:
    b.to_hit += acc.get("to_hit_bonus", 0)
    b.dr += acc.get("dr_bonus", 0)
    b.max_hp += acc.get("max_hp_bonus", 0)
    b.max_energy += acc.get("max_energy_bonus", 0)
    b.dodge += acc.get("dodge_bonus", 0.0)
    b.crit_mult += acc.get("crit_mult_bonus", 0.0)
    b.crit_chance += acc.get("crit_chance_bonus", 0.0)
    b.initiative += acc.get("initiative_bonus", 0)
    b.energy_regen += acc.get("energy_regen_bonus", 0)
    reduction = acc.get("energy_cost_reduction", 0)
    if reduction:
        # Negative cost mod = reduction
        for action in ("move", "attack", "defend", "dash", "ranged_attack", "trap"):
            b.action_cost_mods[action] = (
                b.action_cost_mods.get(action, 0) - reduction
            )
