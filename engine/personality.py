"""Personality profiler — analyze bot behavior and generate profiles.

Consumes match history (stats, actions, equipment) and pattern tables
to produce trait lists, archetype variants, and flavor bios.
"""

from __future__ import annotations

import json
import os
from typing import Any

from engine.personality_traits import archetype_variant, detect_traits, generate_bio

__all__ = ["profile_bot"]

_OPENER_WINDOW = 3


def profile_bot(
    emoji: str,
    results_dir: str,
    patterns_dir: str,
) -> dict[str, Any]:
    """Build a personality profile for a bot from match history.

    Returns dict with keys: traits, archetype_variant, bio.
    """
    matches = _load_bot_matches(emoji, results_dir)
    patterns = _load_patterns(emoji, patterns_dir)

    if not matches:
        return {
            "traits": [],
            "archetype_variant": "Unknown",
            "bio": "A newcomer yet to prove themselves.",
        }

    agg = _aggregate(emoji, matches)
    traits = detect_traits(agg, patterns)
    variant = archetype_variant(agg, traits)
    bio = generate_bio(variant, traits)
    return {"traits": traits, "archetype_variant": variant, "bio": bio}


def _load_bot_matches(emoji: str, results_dir: str) -> list[dict[str, Any]]:
    if not os.path.isdir(results_dir):
        return []
    matches = []
    for fname in os.listdir(results_dir):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(results_dir, fname)) as f:
                data = json.load(f)
            if emoji in data.get("stats", {}):
                matches.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return matches


def _load_patterns(emoji: str, patterns_dir: str) -> dict[str, dict[str, int]]:
    path = os.path.join(patterns_dir, f"{emoji}.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path) as f:
            result: dict[str, dict[str, int]] = json.load(f)
            return result
    except (json.JSONDecodeError, OSError):
        return {}


def _aggregate(emoji: str, matches: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(matches)
    totals = {k: 0.0 for k in ("kills", "damage_dealt", "damage_taken", "rounds_survived", "score", "momentum_tier")}
    action_counts: dict[str, int] = {}
    early_attacks = 0
    total_early = 0
    eq_freq: dict[str, dict[str, int]] = {"weapon": {}, "armor": {}, "tactical": {}}
    wins = 0
    archetypes: dict[str, int] = {}

    for match in matches:
        st = match["stats"].get(emoji, {})
        for k in totals:
            totals[k] += st.get(k, 0)
        if match.get("winner") == emoji:
            wins += 1
        arch = st.get("archetype", "")
        if arch:
            archetypes[arch] = archetypes.get(arch, 0) + 1
        _tally_equipment(eq_freq, st.get("equipment", {}))
        ea, te = _tally_actions(action_counts, match, emoji)
        early_attacks += ea
        total_early += te

    total_actions = sum(action_counts.values()) or 1
    return {
        "matches": n,
        "wins": wins,
        "avg_kills": totals["kills"] / n,
        "avg_damage": totals["damage_dealt"] / n,
        "avg_taken": totals["damage_taken"] / n,
        "avg_survival": totals["rounds_survived"] / n,
        "avg_score": totals["score"] / n,
        "avg_momentum": totals["momentum_tier"] / n,
        "action_ratios": {a: c / total_actions for a, c in action_counts.items()},
        "early_attack_ratio": early_attacks / max(total_early, 1),
        "equipment_freq": eq_freq,
        "top_archetype": max(archetypes, key=lambda k: archetypes[k]) if archetypes else "",
        "win_rate": wins / n,
    }


def _tally_equipment(freq: dict[str, Any], equipment: dict[str, Any]) -> None:
    for slot in ("weapon", "armor", "tactical"):
        val = equipment.get(slot)
        if val:
            freq[slot][val] = freq[slot].get(val, 0) + 1


def _tally_actions(
    counts: dict[str, int],
    match: dict[str, Any],
    emoji: str,
) -> tuple[int, int]:
    early_attacks = 0
    total_early = 0
    for rnd in match.get("rounds", []):
        for pos in rnd.get("positions", []):
            if pos.get("emoji") != emoji:
                continue
            action_raw = pos.get("action", "")
            action = action_raw.split()[0] if action_raw else ""
            if action:
                counts[action] = counts.get(action, 0) + 1
            if rnd.get("round", 99) <= _OPENER_WINDOW:
                total_early += 1
                if action in ("attack", "ranged_attack"):
                    early_attacks += 1
    return early_attacks, total_early
