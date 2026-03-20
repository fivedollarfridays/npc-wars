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
    damage: int
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
) -> int:
    """Compute effective AC for a defender."""
    ac = BASE_AC + defender.damage_reduction
    if defending:
        ac += DEFEND_AC_BONUS
    if momentum_defense_reduct > 0:
        ac = max(1, ac - int(ac * momentum_defense_reduct))
    return ac


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
) -> CombatResult:
    """Resolve whether a roll hits/crits, check dodge, and compute damage."""
    total_roll = d20 + modifier

    if total_roll < ac:
        return CombatResult(
            hit=False, damage=0, roll=d20, modifier=modifier,
            target_ac=ac, is_crit=False, is_miss=True, dodged=False,
        )

    base = rng.randint(min_damage, max_damage)
    is_crit = d20 == 20 or total_roll >= ac + CRIT_THRESHOLD
    if is_crit:
        base = int(base * crit_multiplier)
    damage = max(1, int(base * momentum_damage_mult))

    dodged = rng.random() < dodge_chance / 100
    if dodged:
        damage = max(1, damage // 2)

    return CombatResult(
        hit=True, damage=damage, roll=d20, modifier=modifier,
        target_ac=ac, is_crit=is_crit, is_miss=False, dodged=dodged,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calculate_hit_probability(
    attacker: DerivedStats,
    defender: DerivedStats,
    *,
    defending: bool = False,
    to_hit_modifier: int = 0,
    momentum_defense_reduct: float = 0.0,
) -> dict[str, float]:
    """Pure-math hit probability calculator. No RNG.

    Returns dict with hit_chance, crit_chance, dodge_chance, expected_damage.
    All chances are percentages (0-100).
    """
    modifier = attacker.initiative // 10 + to_hit_modifier
    ac = _compute_ac(defender, defending, momentum_defense_reduct)

    # d20 ranges 1-20; need d20 + modifier >= ac to hit
    min_roll_to_hit = ac - modifier
    if min_roll_to_hit <= 1:
        hit_chance = 100.0
    elif min_roll_to_hit > 20:
        hit_chance = 5.0  # nat 20 always hits
    else:
        hit_chance = (21 - min_roll_to_hit) / 20 * 100

    # Crit: d20 == 20 OR total_roll >= ac + CRIT_THRESHOLD
    crit_min_roll = ac + CRIT_THRESHOLD - modifier
    if crit_min_roll <= 1:
        crit_chance = 100.0
    elif crit_min_roll > 20:
        crit_chance = 5.0  # nat 20 always crits
    else:
        crit_chance = (21 - crit_min_roll) / 20 * 100

    dodge_chance = defender.dodge_chance

    # Expected damage calculation
    avg_damage = (attacker.min_damage + attacker.max_damage) / 2
    avg_crit_damage = avg_damage * attacker.crit_multiplier
    # Weighted average: non-crit hits + crit hits
    crit_frac = crit_chance / 100
    dmg_per_hit = avg_damage * (1 - crit_frac) + avg_crit_damage * crit_frac
    # Dodge reduces damage by half
    dodge_frac = dodge_chance / 100
    dmg_after_dodge = dmg_per_hit * (1 - dodge_frac) + (dmg_per_hit / 2) * dodge_frac
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
) -> CombatResult:
    """Roll a melee attack from *attacker* against *defender*."""
    modifier = attacker.initiative // 10 + to_hit_modifier
    d20 = rng.randint(1, 20)
    ac = _compute_ac(defender, defending, momentum_defense_reduct)

    return _resolve_hit(
        d20, modifier, ac, attacker.min_damage, attacker.max_damage,
        attacker.crit_multiplier, momentum_damage_mult, rng,
        dodge_chance=defender.dodge_chance,
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
) -> CombatResult:
    """Roll a ranged attack — lower accuracy and damage than melee."""
    modifier = attacker.initiative // 10 - RANGED_HIT_PENALTY + to_hit_modifier
    d20 = rng.randint(1, 20)
    ac = _compute_ac(defender, defending, momentum_defense_reduct)

    min_dmg = max(1, int(attacker.min_damage * RANGED_DAMAGE_SCALE))
    max_dmg = max(1, int(attacker.max_damage * RANGED_DAMAGE_SCALE))

    return _resolve_hit(
        d20, modifier, ac, min_dmg, max_dmg,
        attacker.crit_multiplier, momentum_damage_mult, rng,
        dodge_chance=defender.dodge_chance,
    )
