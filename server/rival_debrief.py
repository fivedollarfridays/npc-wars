"""Post-match debrief analysis for rival training matches."""

from __future__ import annotations

from typing import Any

from server.rival_factory import RIVAL_TIERS

__all__ = ["analyze_rival_match"]


def analyze_rival_match(
    match_data: dict[str, Any],
    player_emoji: str,
    rival_tier: int,
    *,
    pattern_data: dict[str, dict[str, float]] | None = None,
    graduated: bool = False,
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
    elif rival_tier == 3:
        analysis = _analyze_economist_lesson(match_data, player_emoji)
    elif rival_tier == 4:
        analysis = _analyze_counter_lesson(match_data, player_emoji, pattern_data)
    elif rival_tier == 5:
        analysis = _analyze_mirror_lesson(match_data, player_emoji, pattern_data)
    else:
        analysis = _default_analysis(match_data, player_emoji, rival_tier)

    result = {
        "tier": rival_tier,
        "rival_name": rival_name,
        "outcome": outcome,
        **analysis,
    }
    if pattern_data:
        result["patterns"] = pattern_data
    if graduated:
        result["ceremony_message"] = (
            "TRAINING COMPLETE -- You've mastered all 5 rival tiers!"
        )
    return result


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


def _collect_energy_data(
    rounds: list[dict[str, Any]],
    player_emoji: str,
    rival_emoji: str,
) -> tuple[list[int], list[float]]:
    """Collect starved_rounds and energy_diffs from match rounds."""
    starved_rounds: list[int] = []
    energy_diffs: list[float] = []
    for rnd in rounds:
        player_pos = _find_pos(rnd, player_emoji)
        rival_pos = _find_pos(rnd, rival_emoji)
        if not player_pos or not rival_pos:
            continue
        p_energy = player_pos.get("energy", 100)
        r_energy = rival_pos.get("energy", 100)
        energy_diffs.append(r_energy - p_energy)
        if p_energy < 20:
            starved_rounds.append(rnd["round"])
    return starved_rounds, energy_diffs


def _analyze_economist_lesson(
    match_data: dict[str, Any],
    player_emoji: str,
) -> dict[str, Any]:
    """Tier 3: find rounds where player was energy-starved."""
    from server.rival_factory import RIVAL_EMOJI

    starved_rounds, energy_diffs = _collect_energy_data(
        match_data.get("rounds", []), player_emoji, RIVAL_EMOJI,
    )
    avg_diff = sum(energy_diffs) / len(energy_diffs) if energy_diffs else 0

    if starved_rounds:
        key_round = starved_rounds[0]
        lesson = f"You ran out of energy in {len(starved_rounds)} rounds"
        what = (
            f"Round {key_round}: Your energy dropped below 20 "
            "while The Economist had reserves"
        )
        tip = "Rest at safe distance when energy < 40. Don't attack every turn."
    else:
        key_round = None
        lesson = "Good energy management -- you kept pace"
        what = f"Average energy differential: {avg_diff:+.0f} in Economist's favor"
        tip = "Keep managing energy efficiently to beat The Economist consistently."

    return {
        "lesson": lesson,
        "what_happened": what,
        "tip": tip,
        "key_round": key_round,
        "energy_starved_rounds": starved_rounds,
    }


_ACTION_COUNTER_MAP: dict[str, str] = {
    "attack": "defend", "rest": "attack", "defend": "attack",
    "move": "attack", "ranged_attack": "move", "dash": "defend",
}


def _rank_patterns(
    pattern_data: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    """Rank player patterns by probability, annotating with counters."""
    ranked: list[dict[str, Any]] = []
    for ctx, actions in pattern_data.items():
        if actions:
            top_action = max(actions, key=actions.get)  # type: ignore[arg-type]
            ranked.append({
                "context": ctx,
                "your_action": top_action,
                "probability": actions[top_action],
                "counter_used": _ACTION_COUNTER_MAP.get(top_action, "move"),
            })
    ranked.sort(key=lambda p: p["probability"], reverse=True)
    return ranked


def _analyze_counter_lesson(
    match_data: dict[str, Any],
    player_emoji: str,
    pattern_data: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Tier 4 debrief: show player patterns and how they were countered."""
    if not pattern_data:
        return {
            "lesson": "The Counter is learning your patterns. "
                      "Play more matches to see analysis.",
            "what_happened": "Not enough data yet for pattern analysis.",
            "tip": "Your patterns become visible after 3+ rival matches.",
            "key_round": None,
        }

    top_patterns = _rank_patterns(pattern_data)

    if top_patterns:
        top = top_patterns[0]
        lesson = (
            f"The Counter read your patterns: you {top['your_action']} "
            f"{top['probability']:.0%} of the time when "
            f"{_format_context(top['context'])}"
        )
        what = (
            f"It countered with '{top['counter_used']}' every time "
            "you were predictable"
        )
        tip = ("Vary your actions. If you always attack when adjacent, "
               "try defending or moving sometimes.")
    else:
        lesson = "The Counter couldn't find strong patterns yet."
        what = "Your actions were varied enough to be unpredictable."
        tip = "Keep varying your strategy to stay ahead."

    return {
        "lesson": lesson,
        "what_happened": what,
        "tip": tip,
        "key_round": None,
        "top_patterns": top_patterns[:3],
    }


def _format_context(ctx: str) -> str:
    """Human-readable context name."""
    return {
        "at_range_1": "adjacent to an enemy",
        "below_30_hp": "below 30 HP",
        "storm_closing": "near the storm",
        "after_damage": "after taking damage",
    }.get(ctx, ctx)


def _analyze_mirror_lesson(
    match_data: dict[str, Any],
    player_emoji: str,
    pattern_data: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Tier 5 debrief: show full adaptation analysis for The Mirror."""
    if not pattern_data:
        return {
            "lesson": "The Mirror adapts to your strategy. "
                      "Play more matches to see how it reads you.",
            "what_happened": "Not enough data yet for Mirror analysis.",
            "tip": "The Mirror learns from every match. "
                   "Be unpredictable to stay ahead.",
            "key_round": None,
        }

    top_patterns = _rank_patterns(pattern_data)

    if top_patterns:
        top = top_patterns[0]
        lesson = (
            f"The Mirror adapted to your strategy: when "
            f"{_format_context(top['context'])}, you "
            f"{top['your_action']} {top['probability']:.0%} of the time "
            f"-- it countered with {top['counter_used']}"
        )
        what = (
            f"Across all contexts, The Mirror predicted your most likely "
            f"action and chose the counter. Your most readable pattern: "
            f"{top['your_action']} when {_format_context(top['context'])}"
        )
        tip = (
            "You've reached the final rival. To beat The Mirror, "
            "be unpredictable -- vary your actions in every context."
        )
    else:
        lesson = "The Mirror couldn't find strong patterns in your play."
        what = "Your actions were varied enough to confuse the adaptation."
        tip = "Keep varying your strategy to stay ahead of The Mirror."

    return {
        "lesson": lesson,
        "what_happened": what,
        "tip": tip,
        "key_round": None,
        "top_patterns": top_patterns[:3],
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
