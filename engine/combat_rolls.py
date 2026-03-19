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
    "CombatResult",
    "roll_attack",
    "roll_ranged_attack",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_AC: int = 5
DEFEND_AC_BONUS: int = 8
CRIT_THRESHOLD: int = 8
RANGED_HIT_PENALTY: int = 2
RANGED_DAMAGE_SCALE: float = 0.6

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
) -> CombatResult:
    """Resolve whether a roll hits/crits and compute damage."""
    total_roll = d20 + modifier

    if total_roll < ac:
        return CombatResult(
            hit=False, damage=0, roll=d20, modifier=modifier,
            target_ac=ac, is_crit=False, is_miss=True,
        )

    base = rng.randint(min_damage, max_damage)
    is_crit = d20 == 20 or total_roll >= ac + CRIT_THRESHOLD
    if is_crit:
        base = int(base * crit_multiplier)
    damage = max(1, int(base * momentum_damage_mult))

    return CombatResult(
        hit=True, damage=damage, roll=d20, modifier=modifier,
        target_ac=ac, is_crit=is_crit, is_miss=False,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def roll_attack(
    attacker: DerivedStats,
    defender: DerivedStats,
    *,
    defending: bool = False,
    rng: random.Random,
    momentum_damage_mult: float = 1.0,
    momentum_defense_reduct: float = 0.0,
) -> CombatResult:
    """Roll a melee attack from *attacker* against *defender*."""
    modifier = attacker.initiative // 10
    d20 = rng.randint(1, 20)
    ac = _compute_ac(defender, defending, momentum_defense_reduct)

    return _resolve_hit(
        d20, modifier, ac, attacker.min_damage, attacker.max_damage,
        attacker.crit_multiplier, momentum_damage_mult, rng,
    )


def roll_ranged_attack(
    attacker: DerivedStats,
    defender: DerivedStats,
    *,
    defending: bool = False,
    rng: random.Random,
    momentum_damage_mult: float = 1.0,
    momentum_defense_reduct: float = 0.0,
) -> CombatResult:
    """Roll a ranged attack — lower accuracy and damage than melee."""
    modifier = attacker.initiative // 10 - RANGED_HIT_PENALTY
    d20 = rng.randint(1, 20)
    ac = _compute_ac(defender, defending, momentum_defense_reduct)

    min_dmg = max(1, int(attacker.min_damage * RANGED_DAMAGE_SCALE))
    max_dmg = max(1, int(attacker.max_damage * RANGED_DAMAGE_SCALE))

    return _resolve_hit(
        d20, modifier, ac, min_dmg, max_dmg,
        attacker.crit_multiplier, momentum_damage_mult, rng,
    )
