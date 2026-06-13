"""Equipment wiring audit — the permanent guard against placebo items.

Walks every bonus field of every weapon/armor/accessory in
``EQUIPMENT_CATALOG`` and asserts the declared field produces an *observable*
engine difference vs. an unequipped control, exercising the real engine paths
(``resolve_attacks``/``roll_attack``, ``_compute_ac``, ``create_bots``,
``Bot.apply_action_cost``, ``apply_energy_and_rest``, initiative sort order,
forced-dodge RNG).

Fields that are declared in the catalog but wired nowhere today
(``initiative_bonus``, ``dodge_bonus``, ``energy_regen_bonus``,
``rest_energy_bonus``, ``crit_chance_bonus``) are marked
``xfail(strict=True)`` — so the suite is green now, and T73.4 (which wires
them) flips each xfail into a real assertion. A new catalog item carrying an
unknown bonus key fails the audit, because no prober exists for it.
"""

from __future__ import annotations

import random
from typing import Any

import pytest

from engine.combat import Bot
from engine.equipment import EQUIPMENT_CATALOG, EquipmentBonuses
from engine.match_setup import create_bots
from engine.rounds import apply_energy_and_rest
from engine.rounds_combat import build_pos_map, resolve_attacks
from engine.stats import DerivedStats

# Categories whose bonuses are aggregated by ``compute_equipment_bonuses``.
AUDITED_CATEGORIES = ("weapon", "armor", "accessory")

# Catalog keys that are not gameplay bonuses (cost is budget; special is a
# weapon tag handled separately in the combat layer).
NON_BONUS_KEYS = {"cost", "special"}

# Fields declared in the catalog but not yet wired into the engine. T73.4
# turns these xfails into real assertions.
DEAD_FIELDS = {
    "initiative_bonus", "dodge_bonus", "energy_regen_bonus",
    "rest_energy_bonus", "crit_chance_bonus",
}


# ── Object builders ─────────────────────────────────────────────────


def _derived(**overrides: Any) -> DerivedStats:
    """Build a DerivedStats with sane defaults, overriding specific fields."""
    defaults = {
        "max_hp": 100, "max_energy": 100, "min_damage": 5, "max_damage": 10,
        "crit_multiplier": 1.5, "dodge_chance": 0.0, "initiative": 25,
        "damage_reduction": 0, "energy_regen": 0,
    }
    defaults.update(overrides)
    return DerivedStats(**defaults)


def _bot(emoji: str, x: int, y: int, derived: DerivedStats | None = None,
         bonuses: EquipmentBonuses | None = None) -> Bot:
    """Build a minimal Bot with optional controlled derived stats/bonuses."""
    b = Bot(name=emoji, emoji=emoji, bio="", author="t",
            decide_func=lambda *a: ("rest",), x=x, y=y)
    if derived is not None:
        b.derived = derived
        b.hp = float(derived.max_hp)
        b.energy = derived.max_energy
    if bonuses is not None:
        b.equipment_bonuses = bonuses
    return b


def _cfg(emoji: str, accessories: list[str]) -> dict[str, Any]:
    """A create_bots config with a fixed weapon/armor and given accessories."""
    return {
        "name": emoji, "emoji": emoji, "bio": "", "author": "t",
        "decide_func": lambda *a: ("rest",),
        "equipment": {
            "weapon": "sword", "armor": "leather",
            "accessories": accessories, "tactical": None,
        },
    }


# ── Engine observers ────────────────────────────────────────────────


def _hits(atk_b: EquipmentBonuses, def_b: EquipmentBonuses,
          atk_der: DerivedStats, def_der: DerivedStats, n: int = 600) -> int:
    """Count melee hits over *n* fixed-seed rolls through resolve_attacks."""
    a = _bot("A", 0, 0, atk_der, atk_b)
    d = _bot("B", 1, 0, def_der, def_b)
    alive = [a, d]
    pos = build_pos_map(alive)
    actions = {"A": ("attack", "east"), "B": ("nothing",)}
    total = 0
    for s in range(n):
        d.hp, d.alive = float(def_der.max_hp), True
        a.hp, a.alive = float(atk_der.max_hp), True
        events = resolve_attacks(alive, actions, pos, rng=random.Random(s))
        total += sum(1 for e in events if e.get("type") == "hit")
    return total


def _damage(atk_b: EquipmentBonuses, atk_der: DerivedStats, n: int = 500) -> float:
    """Sum melee damage over *n* fixed-seed rolls against a 0-DR sponge."""
    def_der = _derived(damage_reduction=0, dodge_chance=0.0, max_hp=10 ** 6)
    a = _bot("A", 0, 0, atk_der, atk_b)
    d = _bot("B", 1, 0, def_der, EquipmentBonuses())
    d.hp = 10 ** 6
    alive = [a, d]
    pos = build_pos_map(alive)
    actions = {"A": ("attack", "east"), "B": ("nothing",)}
    total = 0.0
    for s in range(n):
        events = resolve_attacks(alive, actions, pos, rng=random.Random(s))
        total += sum(e.get("damage", 0) for e in events if e.get("type") == "hit")
    return total


def _crits(atk_b: EquipmentBonuses, n: int = 800) -> int:
    """Count crits over *n* fixed-seed rolls for a given attacker loadout."""
    atk_der = _derived(initiative=0, min_damage=5, max_damage=5)
    def_der = _derived(damage_reduction=0, dodge_chance=0.0, max_hp=10 ** 6)
    a = _bot("A", 0, 0, atk_der, atk_b)
    d = _bot("B", 1, 0, def_der, EquipmentBonuses())
    d.hp = 10 ** 6
    alive = [a, d]
    pos = build_pos_map(alive)
    actions = {"A": ("attack", "east"), "B": ("nothing",)}
    total = 0
    for s in range(n):
        events = resolve_attacks(alive, actions, pos, rng=random.Random(s))
        total += sum(1 for e in events if e.get("is_crit"))
    return total


def _create_bots_delta(item: str, attr: str) -> bool:
    """True if equipping *item* raises bot.<attr> through create_bots."""
    bots = create_bots([_cfg("C", []), _cfg("E", [item])], [(0, 0), (3, 3)])
    return getattr(bots[1], attr) > getattr(bots[0], attr)


# ── Per-field probers: True iff the field has an observable engine effect ──


def probe_to_hit(value: int, item: str) -> bool:
    atk = _derived(initiative=0, min_damage=5, max_damage=5)
    deff = _derived(damage_reduction=0, dodge_chance=0.0)
    ctrl = _hits(EquipmentBonuses(), EquipmentBonuses(), atk, deff)
    eq = _hits(EquipmentBonuses(to_hit=value), EquipmentBonuses(), atk, deff)
    return eq > ctrl if value > 0 else eq < ctrl


def probe_armor_pierce(value: int, item: str) -> bool:
    atk = _derived(initiative=0, min_damage=5, max_damage=5)
    deff = _derived(damage_reduction=6, dodge_chance=0.0)
    ctrl = _hits(EquipmentBonuses(), EquipmentBonuses(), atk, deff)
    eq = _hits(EquipmentBonuses(armor_pierce=value), EquipmentBonuses(), atk, deff)
    return eq > ctrl


def probe_dr(value: int, item: str) -> bool:
    atk = _derived(initiative=0, min_damage=5, max_damage=5)
    deff = _derived(damage_reduction=0, dodge_chance=0.0)
    ctrl = _hits(EquipmentBonuses(), EquipmentBonuses(), atk, deff)
    eq = _hits(EquipmentBonuses(), EquipmentBonuses(dr=value), atk, deff)
    return eq < ctrl


def probe_min_dmg(value: int, item: str) -> bool:
    atk = _derived(initiative=200, min_damage=5, max_damage=20, crit_multiplier=1.0)
    return _damage(EquipmentBonuses(min_damage=value), atk) > _damage(EquipmentBonuses(), atk)


def probe_max_dmg(value: int, item: str) -> bool:
    atk = _derived(initiative=200, min_damage=5, max_damage=20, crit_multiplier=1.0)
    return _damage(EquipmentBonuses(max_damage=value), atk) > _damage(EquipmentBonuses(), atk)


def probe_crit_mult(value: float, item: str) -> bool:
    atk = _derived(initiative=200, min_damage=10, max_damage=10, crit_multiplier=2.0)
    return _damage(EquipmentBonuses(crit_mult=value), atk, 400) > _damage(EquipmentBonuses(), atk, 400)


def probe_reach(value: int, item: str) -> bool:
    def finds_target(reach: int) -> bool:
        a = _bot("A", 0, 0, bonuses=EquipmentBonuses(reach_distance=reach))
        b = _bot("B", value, 0)
        alive = [a, b]
        events = resolve_attacks(
            alive, {"A": ("attack", "east"), "B": ("nothing",)},
            build_pos_map(alive), rng=random.Random(0),
        )
        return any(e.get("target") == "B" for e in events)

    return finds_target(value) and not finds_target(0)


def probe_energy_penalties(value: dict[str, int], item: str) -> bool:
    action = next(iter(value))
    ctrl = _bot("C", 0, 0)
    eq = _bot("E", 1, 0, bonuses=EquipmentBonuses(action_cost_mods=dict(value)))
    c0, e0 = ctrl.energy, eq.energy
    ctrl.apply_action_cost(action)
    eq.apply_action_cost(action)
    return (e0 - eq.energy) > (c0 - ctrl.energy)


def probe_energy_cost_reduction(value: int, item: str) -> bool:
    actions = ("move", "attack", "defend", "dash", "ranged_attack", "trap")
    mods = {a: -value for a in actions}
    ctrl = _bot("C", 0, 0)
    eq = _bot("E", 1, 0, bonuses=EquipmentBonuses(action_cost_mods=mods))
    c0, e0 = ctrl.energy, eq.energy
    ctrl.apply_action_cost("attack")
    eq.apply_action_cost("attack")
    return (e0 - eq.energy) < (c0 - ctrl.energy)


def probe_max_hp(value: int, item: str) -> bool:
    return _create_bots_delta(item, "hp")


def probe_max_energy(value: int, item: str) -> bool:
    return _create_bots_delta(item, "energy")


def probe_initiative(value: int, item: str) -> bool:
    a = _bot("A", 0, 0, _derived(initiative=20), EquipmentBonuses(initiative=value))
    b = _bot("B", 2, 0, _derived(initiative=20))
    t = _bot("T", 1, 0, _derived(max_hp=10 ** 6))
    t.hp = 10 ** 6
    alive = [b, a, t]  # b before a: stable sort keeps b first unless A overtakes
    events = resolve_attacks(
        alive, {"A": ("attack", "east"), "B": ("attack", "west"), "T": ("nothing",)},
        build_pos_map(alive), rng=random.Random(0),
    )
    first = next((e.get("attacker") for e in events if e.get("attacker")), None)
    return first == "A"


def probe_dodge(value: float, item: str) -> bool:
    atk = _derived(initiative=200, min_damage=5, max_damage=5)
    deff = _derived(damage_reduction=0, dodge_chance=0.0, max_hp=10 ** 6)
    a = _bot("A", 0, 0, atk)
    d = _bot("B", 1, 0, deff, EquipmentBonuses(dodge=value))
    d.hp = 10 ** 6
    alive = [a, d]
    pos = build_pos_map(alive)
    actions = {"A": ("attack", "east"), "B": ("nothing",)}
    dodged = 0
    for s in range(800):
        events = resolve_attacks(alive, actions, pos, rng=random.Random(s))
        dodged += sum(1 for e in events if e.get("dodged"))
    return dodged > 0


def probe_crit_chance(value: float, item: str) -> bool:
    return _crits(EquipmentBonuses(crit_chance=value)) > _crits(EquipmentBonuses())


def _probe_rest(value: int, field: str) -> bool:
    der = _derived(max_energy=100, energy_regen=0)
    ctrl = _bot("C", 0, 0, der)
    ctrl.energy = 50
    eq = _bot("E", 1, 0, der, _one_field(field, value))
    eq.energy = 50
    apply_energy_and_rest([ctrl, eq], {"C": ("rest",), "E": ("rest",)}, set())
    return eq.energy > ctrl.energy


def _one_field(field: str, value: int) -> EquipmentBonuses:
    """An EquipmentBonuses with a single scalar field set."""
    b = EquipmentBonuses()
    setattr(b, field, value)
    return b


# ── Field → prober registry ─────────────────────────────────────────

PROBES = {
    "to_hit": probe_to_hit,
    "to_hit_bonus": probe_to_hit,
    "min_dmg": probe_min_dmg,
    "max_dmg": probe_max_dmg,
    "crit_mult_bonus": probe_crit_mult,
    "armor_pierce": probe_armor_pierce,
    "reach_distance": probe_reach,
    "dr_bonus": probe_dr,
    "energy_penalties": probe_energy_penalties,
    "energy_cost_reduction": probe_energy_cost_reduction,
    "max_hp_bonus": probe_max_hp,
    "max_energy_bonus": probe_max_energy,
    "initiative_bonus": probe_initiative,
    "dodge_bonus": probe_dodge,
    "crit_chance_bonus": probe_crit_chance,
    "rest_energy_bonus": lambda v, item: _probe_rest(v, "rest_energy_bonus"),
    "energy_regen_bonus": lambda v, item: _probe_rest(v, "energy_regen"),
}


def _audit_cases() -> list[Any]:
    """One parametrized case per (non-zero) bonus field per catalog item."""
    cases: list[Any] = []
    for category in AUDITED_CATEGORIES:
        for item, spec in EQUIPMENT_CATALOG[category].items():
            for key, value in spec.items():
                if key in NON_BONUS_KEYS:
                    continue
                # Skip legitimately-zero/empty bonuses on known fields; a value
                # of 0 has nothing to observe. Unknown keys are never skipped so
                # they surface as failures below.
                if key in PROBES and not value:
                    continue
                marks = [pytest.mark.xfail(
                    strict=True, reason="dead field — wired in T73.4",
                )] if key in DEAD_FIELDS else []
                cases.append(pytest.param(
                    category, item, key, value,
                    id=f"{category}-{item}-{key}", marks=marks,
                ))
    return cases


@pytest.mark.parametrize("category,item,field,value", _audit_cases())
def test_equipment_field_has_engine_effect(
    category: str, item: str, field: str, value: Any,
) -> None:
    """Every declared catalog bonus must move the engine, or it's a placebo."""
    probe = PROBES.get(field)
    assert probe is not None, (
        f"Unknown bonus key '{field}' in {category}/{item}: add a prober to "
        f"PROBES or remove the placebo field from EQUIPMENT_CATALOG"
    )
    assert probe(value, item), (
        f"{category}/{item}.{field}={value!r} produced no observable engine "
        f"difference vs. an unequipped control"
    )
