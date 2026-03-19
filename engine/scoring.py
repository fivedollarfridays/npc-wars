"""Per-round scoring engine for NPC Wars."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["ScoreEvent", "calculate_round_scores", "LEADER_BOUNTY_POINTS"]

# Scoring table
SURVIVAL_POINTS = 1
KILL_POINTS = 10
FULL_HP_POINTS = 2
DAMAGE_PER_CHUNK = 25  # +1 per 25 hp dealt
CLEAN_KILL_BONUS = 5
LAST_STANDING_POINTS = 15
STORM_SURVIVOR_POINTS = 3
LEADER_BOUNTY_POINTS = 20


@dataclass(frozen=True, slots=True)
class ScoreEvent:
    """One scoring action attributed to a bot."""

    emoji: str
    source: str
    points: int


def _count_kills(emoji: str, events: list[dict[str, Any]]) -> int:
    """Count kill events where *emoji* is the attacker."""
    return sum(
        1 for e in events
        if e.get("type") == "kill" and e.get("attacker") == emoji
    )


def _total_damage_dealt(emoji: str, events: list[dict[str, Any]]) -> int:
    """Sum damage dealt by *emoji* across hit events."""
    return sum(
        e.get("damage", 0) for e in events
        if e.get("type") in ("hit", "ranged_hit") and e.get("attacker") == emoji
    )


def _total_damage_taken(emoji: str, events: list[dict[str, Any]]) -> int:
    """Sum damage taken by *emoji* across hit events."""
    return sum(
        e.get("damage", 0) for e in events
        if e.get("type") in ("hit", "ranged_hit") and e.get("target") == emoji
    )


def _score_one_bot(
    emoji: str, hp: int, round_events: list[dict[str, Any]],
    alive_count: int, storm_just_activated: bool,
) -> tuple[int, list[ScoreEvent]]:
    """Score a single alive bot for one round."""
    total = 0
    events: list[ScoreEvent] = []

    # Survival
    total += SURVIVAL_POINTS
    events.append(ScoreEvent(emoji=emoji, source="survival", points=SURVIVAL_POINTS))

    # Kill points
    kills = _count_kills(emoji, round_events)
    if kills > 0:
        kill_pts = kills * KILL_POINTS
        total += kill_pts
        events.append(ScoreEvent(emoji=emoji, source="kill", points=kill_pts))

    # Damage dealt
    dmg_pts = _total_damage_dealt(emoji, round_events) // DAMAGE_PER_CHUNK
    if dmg_pts > 0:
        total += dmg_pts
        events.append(ScoreEvent(emoji=emoji, source="damage_dealt", points=dmg_pts))

    # Clean kill: got a kill AND took 0 damage
    if kills > 0 and _total_damage_taken(emoji, round_events) == 0:
        total += CLEAN_KILL_BONUS
        events.append(ScoreEvent(emoji=emoji, source="clean_kill", points=CLEAN_KILL_BONUS))

    # Full HP
    if hp == 100:
        total += FULL_HP_POINTS
        events.append(ScoreEvent(emoji=emoji, source="full_hp", points=FULL_HP_POINTS))

    # Storm survivor
    if storm_just_activated:
        total += STORM_SURVIVOR_POINTS
        events.append(ScoreEvent(emoji=emoji, source="storm_survivor", points=STORM_SURVIVOR_POINTS))

    # Last standing
    if alive_count == 1:
        total += LAST_STANDING_POINTS
        events.append(ScoreEvent(emoji=emoji, source="last_standing", points=LAST_STANDING_POINTS))

    return total, events


_INVALID_ATTACKERS = frozenset({"storm", "unknown", ""})


def _find_leader_killers(
    round_events: list[dict[str, Any]], leader_emoji: str,
) -> list[str]:
    """Return emojis of bots who killed the leader this round."""
    return [
        e["attacker"] for e in round_events
        if (
            e.get("type") == "kill"
            and e.get("victim") == leader_emoji
            and e.get("attacker", "") not in _INVALID_ATTACKERS
        )
    ]


def calculate_round_scores(
    bots: list[dict[str, Any]],
    round_events: list[dict[str, Any]],
    round_num: int,
    storm_border: int,
    prev_storm_border: int,
    leader_emoji: str | None = None,
) -> tuple[dict[str, int], list[ScoreEvent]]:
    """Calculate per-round scores for all bots.

    Returns (emoji -> total_points, list of ScoreEvent).
    """
    scores: dict[str, int] = {}
    score_events: list[ScoreEvent] = []
    alive_count = sum(1 for b in bots if b.get("alive", False))
    storm_just_activated = prev_storm_border == 0 and storm_border > 0

    # Determine who killed the leader (if any)
    leader_killers: list[str] = []
    if leader_emoji is not None:
        leader_killers = _find_leader_killers(round_events, leader_emoji)

    for bot in bots:
        emoji = bot["emoji"]
        if not bot.get("alive", False):
            scores[emoji] = 0
            continue

        total, evts = _score_one_bot(
            emoji, bot.get("hp", 0), round_events,
            alive_count, storm_just_activated,
        )

        # Leader bounty
        if emoji in leader_killers:
            total += LEADER_BOUNTY_POINTS
            evts.append(ScoreEvent(
                emoji=emoji, source="leader_bounty", points=LEADER_BOUNTY_POINTS,
            ))

        scores[emoji] = total
        score_events.extend(evts)

    return scores, score_events
