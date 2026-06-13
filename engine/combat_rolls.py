"""D20-based combat roll engine for Agent Wars."""

from __future__ import annotations

import random
from dataclasses import dataclass

from engine.stats import DerivedStats

__all__ = [
    "BASE_AC",
    "DEFEND_AC_BONUS",
    "CRIT_THRESHOLD",
    "RANGED_HIT_PENALTY",
    "RANGED_DAMAGE_SCALE",
    "REST_HIT_BONUS",
    "TAUNT_HIT_PENALTY",
    "CombatResult",
    "roll_attack",
    "roll_ranged_attack",
    "calculate_hit_probability",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_AC: int = 8
DEFEND_AC_BONUS: int = 6
CRIT_THRESHOLD: int = 15
RANGED_HIT_PENALTY: int = 2
RANGED_DAMAGE_SCALE: float = 0.6
REST_HIT_BONUS: int = 3       # +3 to hit resting targets
TAUNT_HIT_PENALTY: int = 3    # -3 when taunted attacking non-taunter

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CombatResult:
    """Outcome of a single attack roll."""

    hit: bool
    damage: float  # includes fractional component for tiebreaking
    roll: int  # d20 result (before modifier)
    modifier: int  # to-hit modifier from initiative
    target_ac: int  # defender's effective AC
    is_crit: bool
    is_miss: bool  # roll + mod < AC
    dodged: bool  # True if defender dodged (damage halved)


# ---------------------------------------------------------------------------
# Roll helpers
# ---------------------------------------------------------------------------


def _compute_ac(
    defender: DerivedStats,
    defending: bool,
    momentum_defense_reduct: float,
    equipment_dr: int = 0,
    armor_pierce: int = 0,
    tactical_dr: int = 0,
    terrain_ac: int = 0,
) -> int:
    """Compute effective AC for a defender.

    *equipment_dr* adds to DR (e.g. plate armor +6).
    *tactical_dr* adds temporary DR from tactical fortify.
    *terrain_ac* adds AC from terrain (e.g. cover +3).
    *armor_pierce* subtracts from total DR before AC calc.
    """
    total_dr = max(0, defender.damage_reduction + equipment_dr + tactical_dr - armor_pierce)
    ac = BASE_AC + total_dr + terrain_ac
    if defending:
        ac += DEFEND_AC_BONUS
    if momentum_defense_reduct > 0:
        ac = max(1, ac - int(ac * momentum_defense_reduct))
    return max(1, ac)


def _crit_threshold_reduction(crit_chance: float) -> int:
    """Convert a crit-chance bonus (percentage points) to a d20 threshold drop.

    Each percentage point of crit chance lowers the crit threshold by one,
    widening the band of rolls that crit (``total_roll >= ac + threshold``).
    A higher bonus therefore makes crits trigger more often.
    """
    if crit_chance <= 0:
        return 0
    return int(round(crit_chance))


def _resolve_hit(
    d20: int,
    modifier: int,
    ac: int,
    min_damage: int,
    max_damage: int,
    crit_multiplier: float,
    momentum_damage_mult: float,
    rng: random.Random,
    dodge_chance: float = 0.0,
    crit_chance: float = 0.0,
) -> CombatResult:
    """Resolve whether a roll hits/crits, check dodge, and compute damage.

    *crit_chance* (percentage points) lowers the effective crit threshold so a
    higher value makes crits trigger more often.
    """
    total_roll = d20 + modifier

    if total_roll < ac:
        return CombatResult(
            hit=False, damage=0, roll=d20, modifier=modifier,
            target_ac=ac, is_crit=False, is_miss=True, dodged=False,
        )

    base = rng.randint(min_damage, max_damage)
    crit_threshold = max(1, CRIT_THRESHOLD - _crit_threshold_reduction(crit_chance))
    is_crit = d20 == 20 or total_roll >= ac + crit_threshold
    if is_crit:
        base = int(base * crit_multiplier)
    whole = max(1, int(base * momentum_damage_mult))
    # Fractional component from roll for natural HP tiebreaking
    fraction = d20 * 0.01
    damage = whole + fraction

    dodged = rng.random() < dodge_chance / 100
    if dodged:
        damage = max(1.0, damage / 2)

    return CombatResult(
        hit=True, damage=round(damage, 2), roll=d20, modifier=modifier,
        target_ac=ac, is_crit=is_crit, is_miss=False, dodged=dodged,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _d20_chance(min_roll_needed: int) -> float:
    """Percentage chance of rolling *min_roll_needed* or higher on a d20.

    Natural 20 always succeeds (minimum 5%).
    """
    if min_roll_needed <= 1:
        return 100.0
    if min_roll_needed > 20:
        return 5.0  # nat 20 always succeeds
    return (21 - min_roll_needed) / 20 * 100


def calculate_hit_probability(
    attacker: DerivedStats,
    defender: DerivedStats,
    *,
    defending: bool = False,
    to_hit_modifier: int = 0,
    momentum_defense_reduct: float = 0.0,
    equipment_initiative: int = 0,
    equipment_to_hit: int = 0,
    equipment_dodge: float = 0.0,
    equipment_crit_chance: float = 0.0,
) -> dict[str, float]:
    """Pure-math hit probability calculator. No RNG.

    Returns dict with hit_chance, crit_chance, dodge_chance, expected_damage.
    All chances are percentages (0-100). Mirrors ``roll_attack`` equipment
    wiring so the reported numbers match the rolled outcomes.
    """
    modifier = (
        (attacker.initiative + equipment_initiative) // 10
        + to_hit_modifier + equipment_to_hit
    )
    ac = _compute_ac(defender, defending, momentum_defense_reduct)

    crit_threshold = max(1, CRIT_THRESHOLD - _crit_threshold_reduction(equipment_crit_chance))
    hit_chance = _d20_chance(ac - modifier)
    crit_chance = _d20_chance(ac + crit_threshold - modifier)
    dodge_chance = defender.dodge_chance + equipment_dodge

    # Expected damage: weighted by crit rate, dodge rate, and hit rate
    avg_damage = (attacker.min_damage + attacker.max_damage) / 2
    crit_frac = crit_chance / 100
    dmg_per_hit = avg_damage * (1 - crit_frac) + avg_damage * attacker.crit_multiplier * crit_frac
    dodge_frac = dodge_chance / 100
    dmg_after_dodge = dmg_per_hit * (1 - dodge_frac / 2)
    expected_damage = dmg_after_dodge * hit_chance / 100

    return {
        "hit_chance": round(hit_chance, 1),
        "crit_chance": round(crit_chance, 1),
        "dodge_chance": round(dodge_chance, 1),
        "expected_damage": round(expected_damage, 1),
    }


def roll_attack(
    attacker: DerivedStats,
    defender: DerivedStats,
    *,
    defending: bool = False,
    rng: random.Random,
    momentum_damage_mult: float = 1.0,
    momentum_defense_reduct: float = 0.0,
    to_hit_modifier: int = 0,
    equipment_to_hit: int = 0,
    equipment_initiative: int = 0,
    equipment_dodge: float = 0.0,
    equipment_crit_chance: float = 0.0,
    equipment_min_dmg: int = 0,
    equipment_max_dmg: int = 0,
    equipment_crit_mult: float = 0.0,
    equipment_dr: int = 0,
    armor_pierce: int = 0,
    tactical_dr: int = 0,
    terrain_ac: int = 0,
) -> CombatResult:
    """Roll a melee attack from *attacker* against *defender*."""
    modifier = (attacker.initiative + equipment_initiative) // 10 + to_hit_modifier + equipment_to_hit
    d20 = rng.randint(1, 20)
    ac = _compute_ac(
        defender, defending, momentum_defense_reduct,
        equipment_dr=equipment_dr, armor_pierce=armor_pierce,
        tactical_dr=tactical_dr, terrain_ac=terrain_ac,
    )
    min_dmg = attacker.min_damage + equipment_min_dmg
    max_dmg = attacker.max_damage + equipment_max_dmg
    crit_mult = attacker.crit_multiplier + equipment_crit_mult

    return _resolve_hit(
        d20, modifier, ac, min_dmg, max_dmg,
        crit_mult, momentum_damage_mult, rng,
        dodge_chance=defender.dodge_chance + equipment_dodge,
        crit_chance=equipment_crit_chance,
    )


def roll_ranged_attack(
    attacker: DerivedStats,
    defender: DerivedStats,
    *,
    defending: bool = False,
    rng: random.Random,
    momentum_damage_mult: float = 1.0,
    momentum_defense_reduct: float = 0.0,
    to_hit_modifier: int = 0,
    equipment_to_hit: int = 0,
    equipment_initiative: int = 0,
    equipment_dodge: float = 0.0,
    equipment_crit_chance: float = 0.0,
    equipment_min_dmg: int = 0,
    equipment_max_dmg: int = 0,
    equipment_crit_mult: float = 0.0,
    equipment_dr: int = 0,
    armor_pierce: int = 0,
    tactical_dr: int = 0,
    terrain_ac: int = 0,
) -> CombatResult:
    """Roll a ranged attack -- lower accuracy and damage than melee."""
    modifier = (
        (attacker.initiative + equipment_initiative) // 10 - RANGED_HIT_PENALTY
        + to_hit_modifier + equipment_to_hit
    )
    d20 = rng.randint(1, 20)
    ac = _compute_ac(
        defender, defending, momentum_defense_reduct,
        equipment_dr=equipment_dr, armor_pierce=armor_pierce,
        tactical_dr=tactical_dr, terrain_ac=terrain_ac,
    )

    min_dmg = max(1, int(attacker.min_damage * RANGED_DAMAGE_SCALE)) + equipment_min_dmg
    max_dmg = max(1, int(attacker.max_damage * RANGED_DAMAGE_SCALE)) + equipment_max_dmg
    crit_mult = attacker.crit_multiplier + equipment_crit_mult

    return _resolve_hit(
        d20, modifier, ac, min_dmg, max_dmg,
        crit_mult, momentum_damage_mult, rng,
        dodge_chance=defender.dodge_chance + equipment_dodge,
        crit_chance=equipment_crit_chance,
    )
