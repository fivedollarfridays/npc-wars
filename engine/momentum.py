"""Momentum tier system — converts score into gameplay advantages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.combat import Bot

__all__ = [
    "MomentumTier", "TIERS",
    "get_tier", "get_tier_name",
    "apply_momentum_bonuses", "calculate_carryover",
]

CARRYOVER_PERCENT = 0.5
CARRYOVER_CAP = 50

ENERGY_BONUS = 5
DAMAGE_MULTIPLIER = 1.1
DEFENSE_REDUCTION = 0.15


@dataclass(frozen=True, slots=True)
class MomentumTier:
    """Definition of a momentum tier."""

    tier: int
    name: str
    threshold: int


TIERS: list[MomentumTier] = [
    MomentumTier(tier=0, name="", threshold=0),
    MomentumTier(tier=1, name="Momentum", threshold=10),
    MomentumTier(tier=2, name="Battle Fury", threshold=25),
    MomentumTier(tier=3, name="Crowd Favorite", threshold=40),
    MomentumTier(tier=4, name="Unstoppable", threshold=60),
]


def get_tier(score: int) -> int:
    """Return the tier number (0-4) for a given score."""
    result = 0
    for t in TIERS:
        if score >= t.threshold:
            result = t.tier
    return result


def get_tier_name(score: int) -> str:
    """Return the tier name for a given score."""
    tier_num = get_tier(score)
    return TIERS[tier_num].name


def apply_momentum_bonuses(bot: Bot) -> None:
    """Apply cumulative momentum bonuses based on bot.score.

    Tier 1+: +5 energy regen per round (momentum_energy_bonus)
    Tier 2+: +10% damage dealt (momentum_damage_multiplier)
    Tier 3:  Crowd Favorite — visual only, no stat bonus
    Tier 4:  -15% incoming damage (momentum_defense_reduction)
    """
    tier_num = get_tier(bot.score)
    bot.momentum_tier = tier_num

    # Reset to defaults
    bot.momentum_energy_bonus = 0
    bot.momentum_damage_multiplier = 1.0
    bot.momentum_defense_reduction = 0.0

    if tier_num >= 1:
        bot.momentum_energy_bonus = ENERGY_BONUS
    if tier_num >= 2:
        bot.momentum_damage_multiplier = DAMAGE_MULTIPLIER
    if tier_num >= 4:
        bot.momentum_defense_reduction = DEFENSE_REDUCTION


def calculate_carryover(score: int, *, is_winner: bool) -> int:
    """Calculate score carryover for next match.

    Winners carry 50% of final score, capped at 50. Non-winners get 0.
    """
    if not is_winner:
        return 0
    return min(int(score * CARRYOVER_PERCENT), CARRYOVER_CAP)
