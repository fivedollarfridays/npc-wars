"""Post-match debrief analysis for rival training matches."""

from __future__ import annotations

from typing import Any

from server.rival_factory import RIVAL_TIERS

__all__ = ["analyze_rival_match"]


def analyze_rival_match(
    match_data: dict[str, Any],
    player_emoji: str,
    rival_tier: int,
) -> dict[str, Any]:
    """Analyze a rival match and produce a pedagogical debrief."""
    tier_config = RIVAL_TIERS.get(rival_tier, {})
    rival_name = tier_config.get("name", f"Rival Tier {rival_tier}")

    winner = match_data.get("winner", "")
    outcome = "win" if winner == player_emoji else "loss"

    if rival_tier == 1:
        analysis = _analyze_bully_lesson(match_data, player_emoji)
    elif rival_tier == 2:
        analysis = _analyze_storm_lesson(match_data, player_emoji)
    else:
        analysis = _default_analysis(match_data, player_emoji, rival_tier)

    return {
        "tier": rival_tier,
        "rival_name": rival_name,
        "outcome": outcome,
        **analysis,
    }


def _analyze_bully_lesson(
    match_data: dict[str, Any],
    player_emoji: str,
) -> dict[str, Any]:
    """Tier 1: find rounds where player rested adjacent to the rival."""
    punished_rounds: list[int] = []
    key_round: int | None = None

    for rnd in match_data.get("rounds", []):
        player_pos = _find_pos(rnd, player_emoji)
        if player_pos is None:
            continue
        if player_pos.get("action") != "rest":
            continue
        for pos in rnd.get("positions", []):
            if pos["emoji"] == player_emoji:
                continue
            if _adjacent(player_pos, pos):
                punished_rounds.append(rnd["round"])
                if key_round is None:
                    key_round = rnd["round"]
                break

    if punished_rounds:
        lesson = (
            f"You rested next to an enemy in {len(punished_rounds)} round(s). "
            "The Bully punishes passive play -- never rest adjacent to a threat."
        )
        what = (
            f"Round {punished_rounds[0]}: you chose rest while an enemy "
            "was right next to you, giving them a free attack."
        )
    else:
        lesson = "The Bully punishes passive play. Stay alert near enemies."
        what = "No obvious rest-adjacent moments detected."

    return {
        "lesson": lesson,
        "what_happened": what,
        "tip": "Move away or attack instead of resting when enemies are close.",
        "key_round": key_round,
        "punished_rounds": punished_rounds,
    }


def _analyze_storm_lesson(
    match_data: dict[str, Any],
    player_emoji: str,
) -> dict[str, Any]:
    """Tier 2: find rounds where player took storm damage."""
    storm_rounds: list[int] = []
    key_round: int | None = None

    for rnd in match_data.get("rounds", []):
        for evt in rnd.get("events", []):
            if (
                evt.get("type") == "storm_damage"
                and evt.get("target") == player_emoji
            ):
                storm_rounds.append(rnd["round"])
                if key_round is None:
                    key_round = rnd["round"]
                break

    if storm_rounds:
        lesson = (
            f"You took storm damage in {len(storm_rounds)} round(s). "
            "Position toward the center before the storm closes in."
        )
        what = (
            f"Round {storm_rounds[0]}: you were caught in the storm "
            "while the rival stayed safe near the center."
        )
    else:
        lesson = "Good positioning! Keep moving toward center in late rounds."
        what = "No storm damage taken."

    return {
        "lesson": lesson,
        "what_happened": what,
        "tip": "Start moving toward center by round 8 -- don't wait for storm damage.",
        "key_round": key_round,
        "storm_rounds": storm_rounds,
    }


def _default_analysis(
    match_data: dict[str, Any],
    player_emoji: str,
    rival_tier: int,
) -> dict[str, Any]:
    """Generic debrief for tiers 3-5."""
    tier_config = RIVAL_TIERS.get(rival_tier, {})
    name = tier_config.get("name", f"Tier {rival_tier}")
    bio = tier_config.get("bio", "")
    return {
        "lesson": f"{name} tests advanced skills. {bio}",
        "what_happened": "Review the replay to study the rival's patterns.",
        "tip": "Watch the replay and adapt your strategy.",
        "key_round": None,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_pos(
    rnd: dict[str, Any], emoji: str,
) -> dict[str, Any] | None:
    """Find a bot's position entry in a round."""
    for pos in rnd.get("positions", []):
        if pos.get("emoji") == emoji:
            return pos
    return None


def _adjacent(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Check if two positions are within Manhattan distance 1."""
    return abs(a["x"] - b["x"]) + abs(a["y"] - b["y"]) <= 1
