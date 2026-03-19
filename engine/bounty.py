"""Bounty placement and reward system for NPC Wars.

Human-controlled bots have bounties placed on them. Killing a bounty
target rewards the killer with full HP/energy restore and a temporary
damage bonus.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.combat import Bot

__all__ = [
    "BOUNTY_SCALING",
    "BountyInfo",
    "place_bounties",
    "claim_bounty",
    "apply_bounty_reward",
]

# Scaling rules keyed by human count (4+ uses key 3).
# hp_restore: "full" or "none"; bonus_damage_rounds: int.
BOUNTY_SCALING: dict[int, dict[str, Any]] = {
    1: {"hp_restore": "full", "bonus_damage_rounds": 3},
    2: {"hp_restore": "full", "bonus_damage_rounds": 2},
    3: {"hp_restore": "none", "bonus_damage_rounds": 1},
}


@dataclass
class BountyInfo:
    """A bounty placed on a human-controlled bot."""

    target_emoji: str
    reward: str = "full_restore"
    hp_restore: str = "full"
    bonus_damage_rounds: int = 3


def place_bounties(
    bots: list[Bot],
    human_emojis: set[str],
) -> list[BountyInfo]:
    """Create bounties for each human-controlled bot.

    Returns an empty list when no humans are present (pure bot match).
    """
    if not human_emojis:
        return []
    count = len(human_emojis)
    scale = BOUNTY_SCALING.get(count, BOUNTY_SCALING[3])
    return [
        BountyInfo(
            target_emoji=emoji,
            hp_restore=scale["hp_restore"],
            bonus_damage_rounds=scale["bonus_damage_rounds"],
        )
        for emoji in sorted(human_emojis)
    ]


def claim_bounty(
    target_emoji: str,
    bounties: list[BountyInfo],
) -> dict[str, Any] | None:
    """Check if a killed target has a bounty and return the reward.

    Returns a reward dict on match, None otherwise.
    """
    for bounty in bounties:
        if bounty.target_emoji == target_emoji:
            return {
                "hp_restore": bounty.hp_restore,
                "energy_restore": "full",
                "damage_bonus": 0.5,
                "bonus_rounds": bounty.bonus_damage_rounds,
            }
    return None


def apply_bounty_reward(bot: Bot, reward: dict[str, Any]) -> None:
    """Apply bounty reward to the killer bot.

    Restores HP and energy to max, and sets a temporary damage bonus.
    """
    if reward["hp_restore"] != "none":
        bot.hp = bot.derived.max_hp
    bot.energy = bot.derived.max_energy
    bot.damage_bonus = {
        "multiplier": 1.0 + float(reward["damage_bonus"]),
        "rounds_remaining": int(reward["bonus_rounds"]),
    }
