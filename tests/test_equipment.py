"""Tests for engine/equipment.py — equipment catalog, validation, and bonuses."""

from engine.equipment import (
    EQUIPMENT_BUDGET,
    EQUIPMENT_CATALOG,
    EQUIPMENT_DEFAULTS,
    EquipmentBonuses,
    compute_equipment_bonuses,
    validate_equipment,
)


# ── Cycle 1: Catalog structure ──────────────────────────────────────


def test_budget_is_40() -> None:
    assert EQUIPMENT_BUDGET == 40


def test_defaults_are_sword_leather() -> None:
    assert EQUIPMENT_DEFAULTS["weapon"] == "sword"
    assert EQUIPMENT_DEFAULTS["armor"] == "leather"
    assert EQUIPMENT_DEFAULTS["accessories"] == []
    assert EQUIPMENT_DEFAULTS["tactical"] is None


def test_equipment_bonuses_dataclass_defaults() -> None:
    b = EquipmentBonuses()
    assert b.to_hit == 0
    assert b.dr == 0
    assert b.action_cost_mods == {}
    assert b.special_weapon == ""


def test_catalog_has_four_slots() -> None:
    assert set(EQUIPMENT_CATALOG.keys()) == {"weapon", "armor", "accessory", "tactical"}


def test_catalog_has_6_weapons() -> None:
    assert len(EQUIPMENT_CATALOG["weapon"]) == 6


def test_catalog_has_5_armors() -> None:
    assert len(EQUIPMENT_CATALOG["armor"]) == 5


def test_catalog_has_8_accessories() -> None:
    assert len(EQUIPMENT_CATALOG["accessory"]) == 8


def test_catalog_has_4_tacticals() -> None:
    assert len(EQUIPMENT_CATALOG["tactical"]) == 4


def test_catalog_total_23_items() -> None:
    total = sum(len(items) for items in EQUIPMENT_CATALOG.values())
    assert total == 23


def test_every_item_has_cost() -> None:
    for slot, items in EQUIPMENT_CATALOG.items():
        for name, item in items.items():
            assert "cost" in item, f"{slot}/{name} missing cost"
            assert isinstance(item["cost"], int), f"{slot}/{name} cost not int"


# ── Cycle 2: Validation ─────────────────────────────────────────────


def test_default_equipment_validates() -> None:
    sel = {"weapon": "sword", "armor": "leather", "accessories": [], "tactical": None}
    ok, msg = validate_equipment(sel)
    assert ok is True
    assert "14/40" in msg  # sword=8 + leather=6


def test_over_budget_rejected() -> None:
    sel = {
        "weapon": "axe",        # 9
        "armor": "crystal",     # 14
        "accessories": ["cloak_of_shadows", "boots_of_speed"],  # 7+6=13
        "tactical": "battle_cry",  # 8 → total 44
    }
    ok, msg = validate_equipment(sel)
    assert ok is False
    assert "Over budget" in msg


def test_missing_weapon_rejected() -> None:
    sel = {"armor": "leather", "accessories": [], "tactical": None}
    ok, msg = validate_equipment(sel)
    assert ok is False
    assert "weapon" in msg.lower()


def test_missing_armor_rejected() -> None:
    sel = {"weapon": "sword", "accessories": [], "tactical": None}
    ok, msg = validate_equipment(sel)
    assert ok is False
    assert "armor" in msg.lower()


def test_three_accessories_rejected() -> None:
    sel = {
        "weapon": "dagger", "armor": "leather",
        "accessories": ["compass", "ring_of_health", "charm_of_evasion"],
        "tactical": None,
    }
    ok, msg = validate_equipment(sel)
    assert ok is False
    assert "Max 2" in msg


def test_unknown_weapon_rejected() -> None:
    sel = {"weapon": "bazooka", "armor": "leather", "accessories": [], "tactical": None}
    ok, msg = validate_equipment(sel)
    assert ok is False


def test_unknown_accessory_rejected() -> None:
    sel = {
        "weapon": "sword", "armor": "leather",
        "accessories": ["magic_ring"],
        "tactical": None,
    }
    ok, msg = validate_equipment(sel)
    assert ok is False
    assert "Unknown accessory" in msg


def test_unknown_tactical_rejected() -> None:
    sel = {
        "weapon": "sword", "armor": "leather",
        "accessories": [],
        "tactical": "nuke",
    }
    ok, msg = validate_equipment(sel)
    assert ok is False
    assert "Unknown tactical" in msg


def test_valid_full_loadout() -> None:
    sel = {
        "weapon": "dagger",     # 5
        "armor": "leather",     # 6
        "accessories": ["compass", "ring_of_health"],  # 3+4=7
        "tactical": "battle_cry",  # 8 → total 26
    }
    ok, msg = validate_equipment(sel)
    assert ok is True
    assert "26/40" in msg


def test_valid_max_budget_loadout() -> None:
    sel = {
        "weapon": "sword",      # 8
        "armor": "plate",       # 11
        "accessories": ["amulet_of_crit", "boots_of_speed"],  # 6+6=12
        "tactical": None,       # total 37
    }
    ok, msg = validate_equipment(sel)
    assert ok is True


# ── Cycle 3: Bonus computation ───────────────────────────────────────


def test_bonuses_default_loadout() -> None:
    sel = {"weapon": "sword", "armor": "leather", "accessories": [], "tactical": None}
    b = compute_equipment_bonuses(sel)
    assert b.to_hit == 1        # sword +1
    assert b.min_damage == 3    # sword +3
    assert b.max_damage == 5    # sword +5
    assert b.dr == 2            # leather +2
    assert b.special_weapon == "versatile"


def test_axe_gives_crit_mult() -> None:
    sel = {"weapon": "axe", "armor": "leather", "accessories": []}
    b = compute_equipment_bonuses(sel)
    assert b.crit_mult == 0.2
    assert b.to_hit == -1
    assert b.special_weapon == "high_variance"


def test_mace_gives_armor_pierce() -> None:
    sel = {"weapon": "mace", "armor": "leather", "accessories": []}
    b = compute_equipment_bonuses(sel)
    assert b.armor_pierce == 4
    assert b.special_weapon == "armor_piercing"


def test_spear_gives_reach_distance() -> None:
    sel = {"weapon": "spear", "armor": "leather", "accessories": []}
    b = compute_equipment_bonuses(sel)
    assert b.reach_distance == 2
    assert b.special_weapon == "reach"


def test_crystal_gives_rest_energy_bonus() -> None:
    sel = {"weapon": "dagger", "armor": "crystal", "accessories": []}
    b = compute_equipment_bonuses(sel)
    assert b.rest_energy_bonus == 1
    assert b.dr == 1  # crystal only +1 DR


def test_chain_mail_energy_penalties() -> None:
    sel = {"weapon": "dagger", "armor": "chain_mail", "accessories": []}
    b = compute_equipment_bonuses(sel)
    assert b.action_cost_mods["move"] == 2
    assert b.action_cost_mods["attack"] == 2
    assert b.action_cost_mods["defend"] == 2
    assert b.action_cost_mods["dash"] == 2
    assert b.action_cost_mods["ranged_attack"] == 2
    assert b.action_cost_mods["trap"] == 2


def test_two_accessories_stack() -> None:
    sel = {
        "weapon": "dagger", "armor": "leather",
        "accessories": ["ring_of_health", "pendant_of_mind"],
    }
    b = compute_equipment_bonuses(sel)
    assert b.max_hp == 10       # ring_of_health
    assert b.max_energy == 10   # pendant_of_mind
    assert b.energy_regen == 2  # pendant_of_mind


def test_empty_accessories_no_bonus() -> None:
    sel = {"weapon": "dagger", "armor": "leather", "accessories": []}
    b = compute_equipment_bonuses(sel)
    assert b.max_hp == 0
    assert b.max_energy == 0
    assert b.initiative == 0
    assert b.dodge == 0.0


def test_amulet_of_crit_bonuses() -> None:
    sel = {"weapon": "dagger", "armor": "leather", "accessories": ["amulet_of_crit"]}
    b = compute_equipment_bonuses(sel)
    assert b.crit_mult == 0.3
    assert b.crit_chance == 5.0


def test_ring_of_haste_energy_reduction() -> None:
    sel = {"weapon": "dagger", "armor": "leather", "accessories": ["ring_of_haste"]}
    b = compute_equipment_bonuses(sel)
    assert b.initiative == 2
    # energy_cost_reduction=1 gives -1 to all actions
    assert b.action_cost_mods["attack"] == -1
    assert b.action_cost_mods["move"] == -1


def test_boots_of_speed_initiative() -> None:
    sel = {"weapon": "dagger", "armor": "leather", "accessories": ["boots_of_speed"]}
    b = compute_equipment_bonuses(sel)
    assert b.initiative == 5


def test_compass_to_hit() -> None:
    sel = {"weapon": "dagger", "armor": "leather", "accessories": ["compass"]}
    b = compute_equipment_bonuses(sel)
    assert b.to_hit == 3  # dagger +2, compass +1


def test_cloak_of_shadows_dr() -> None:
    sel = {"weapon": "dagger", "armor": "leather", "accessories": ["cloak_of_shadows"]}
    b = compute_equipment_bonuses(sel)
    assert b.dr == 5  # leather +2, cloak +3


def test_charm_of_evasion_dodge() -> None:
    sel = {"weapon": "dagger", "armor": "leather", "accessories": ["charm_of_evasion"]}
    b = compute_equipment_bonuses(sel)
    assert b.dodge == 3.0
