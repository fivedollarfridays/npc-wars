"""XP calculation engine — pure functions, no DB, no I/O."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["XpBreakdown", "calculate_match_xp"]

# XP reward table
BASE_XP = 10
XP_PER_KILL = 15
XP_PER_ROUND = 2
WIN_BONUS = 50
SECOND_PLACE_BONUS = 25
THIRD_PLACE_BONUS = 15
FIRST_BLOOD_XP = 20
LEADER_BOUNTY_XP = 25


@dataclass(frozen=True, slots=True)
class XpBreakdown:
    """XP breakdown for a single bot in a match."""

    base: int
    kills: int
    survival: int
    placement: int
    bonuses: int

    @property
    def total(self) -> int:
        return self.base + self.kills + self.survival + self.placement + self.bonuses


def _placement_xp(placement: int) -> int:
    """Return placement XP for a given finishing position (1-indexed)."""
    if placement == 1:
        return WIN_BONUS
    if placement == 2:
        return SECOND_PLACE_BONUS
    if placement == 3:
        return THIRD_PLACE_BONUS
    return 0


def _bonus_xp(
    *, is_first_blood: bool, killed_leader: bool,
) -> int:
    """Calculate bonus XP from first blood and leader bounty."""
    total = 0
    if is_first_blood:
        total += FIRST_BLOOD_XP
    if killed_leader:
        total += LEADER_BOUNTY_XP
    return total


def _determine_placements(
    match_result: dict[str, Any],
) -> dict[str, int]:
    """Determine finishing placement for each bot (1-indexed).

    Winner is always 1st. Remaining bots ranked by elimination order
    (later elimination = higher placement). Ties share the higher rank.
    """
    winner = match_result.get("winner", "none")
    eliminations = match_result.get("eliminations", [])
    player_emojis = {p["emoji"] for p in match_result["players"]}

    placements: dict[str, int] = {}

    # Eliminated bots: sort by round descending (last eliminated = best rank)
    elims_sorted = sorted(eliminations, key=lambda e: e["round"], reverse=True)

    # Winner gets 1st place
    if winner != "none" and winner in player_emojis:
        placements[winner] = 1
        next_rank = 2
    else:
        next_rank = 1

    # Assign ranks from elimination order (latest elimination first)
    # Uses competition ranking: ties share a rank, next rank skips
    # e.g. two tied 2nd → next is 4th, not 3rd
    prev_round: int | None = None
    current_rank = next_rank
    tie_count = 0
    for elim in elims_sorted:
        emoji = elim["emoji"]
        if emoji in placements:
            continue
        rnd = elim["round"]
        if prev_round is not None and rnd == prev_round:
            # Same round = same rank (tie)
            placements[emoji] = current_rank
            tie_count += 1
        else:
            current_rank = next_rank
            placements[emoji] = current_rank
            tie_count = 0
        prev_round = rnd
        next_rank = current_rank + 1 + tie_count

    # Any remaining bots not eliminated and not winner (edge case)
    for emoji in player_emojis:
        if emoji not in placements:
            placements[emoji] = next_rank
            next_rank += 1

    return placements


def _find_first_blood_killer(eliminations: list[dict[str, Any]]) -> str | None:
    """Find the emoji of the bot who got the first combat kill."""
    for elim in sorted(eliminations, key=lambda e: e["round"]):
        if elim.get("cause") == "combat" and elim.get("killed_by") not in (
            "storm", "tiebreaker", "plague", "none",
        ):
            return str(elim["killed_by"])
    return None


def _find_leader_bounty_killers(
    rounds: list[dict[str, Any]],
) -> set[str]:
    """Find all bots that earned a leader bounty during the match."""
    killers: set[str] = set()
    for rnd in rounds:
        for event in rnd.get("events", []):
            if event.get("type") == "leader_bounty":
                killers.add(event["killer"])
    return killers


def calculate_match_xp(
    match_result: dict[str, Any],
) -> dict[str, XpBreakdown]:
    """Calculate XP earned per bot from a match result.

    Pure function: no DB, no I/O, no side effects.
    """
    stats = match_result.get("stats", {})
    eliminations = match_result.get("eliminations", [])
    rounds = match_result.get("rounds", [])

    placements = _determine_placements(match_result)
    first_blood_killer = _find_first_blood_killer(eliminations)
    leader_bounty_killers = _find_leader_bounty_killers(rounds)

    result: dict[str, XpBreakdown] = {}
    for player in match_result["players"]:
        emoji = player["emoji"]
        bot_stats = stats.get(emoji, {})

        kill_count = bot_stats.get("kills", 0)
        rounds_survived = bot_stats.get("rounds_survived", 0)
        placement = placements.get(emoji, 99)

        bonuses = _bonus_xp(
            is_first_blood=(emoji == first_blood_killer),
            killed_leader=(emoji in leader_bounty_killers),
        )

        result[emoji] = XpBreakdown(
            base=BASE_XP,
            kills=kill_count * XP_PER_KILL,
            survival=rounds_survived * XP_PER_ROUND,
            placement=_placement_xp(placement),
            bonuses=bonuses,
        )

    return result
