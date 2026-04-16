"""Episode generator — game-agnostic episode orchestrator.

Consumes match data, commentary, highlights, personality profiles,
rivalry data, and season standings.  Produces an episode manifest dict
with four sections: cold_open, pre_match, match_commentary, post_match.

Works for both Kill Switch and Code Circuit via platform contracts.
"""

from __future__ import annotations

from typing import Any

__all__ = ["build_episode"]

_DEFAULT_PROFILE: dict[str, Any] = {
    "traits": [],
    "archetype_variant": "Unknown",
    "bio": "A newcomer yet to prove themselves.",
}


def build_episode(
    match_data: dict[str, Any],
    commentary: list[dict[str, Any]],
    highlights: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
    rivalries: list[dict[str, Any]],
    season_standings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a complete episode manifest from match inputs.

    Returns dict with keys: metadata, cold_open, pre_match,
    match_commentary, post_match.
    """
    game = match_data.get("game", "unknown")
    participants = _extract_participants(match_data)

    return {
        "metadata": _build_metadata(match_data, game),
        "cold_open": _build_cold_open(rivalries),
        "pre_match": _build_pre_match(participants, profiles),
        "match_commentary": _build_match_commentary(commentary),
        "post_match": _build_post_match(match_data, highlights, season_standings),
    }


def _build_metadata(match_data: dict[str, Any], game: str) -> dict[str, Any]:
    """Episode metadata: game type, participants, winner."""
    return {
        "game": game,
        "winner": match_data.get("winner"),
        "participants": [p.get("emoji", p.get("name", "?")) for p in match_data.get("players", [])],
    }


def _extract_participants(match_data: dict[str, Any]) -> list[dict[str, str]]:
    """Extract participant list with emoji and name."""
    return [
        {"emoji": p.get("emoji", "?"), "name": p.get("name", "?")}
        for p in match_data.get("players", [])
    ]


def _build_cold_open(rivalries: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate cold open with rivalry recaps and meta narrative."""
    hooks = _collect_rivalry_hooks(rivalries)
    text = _previously_on_text(hooks)
    return {"text": text, "rivalries": hooks}


def _collect_rivalry_hooks(rivalries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract narrative-ready rivalry summaries."""
    hooks: list[dict[str, Any]] = []
    for r in rivalries:
        hooks.append({
            "pair": (r.get("emoji_a") or r.get("car_a", "?"),
                     r.get("emoji_b") or r.get("car_b", "?")),
            "score": r.get("rivalry_score", 0),
            "matches": r.get("matches", 0),
            "narrative": r.get("narrative_hooks", []),
        })
    return hooks


def _previously_on_text(hooks: list[dict[str, Any]]) -> str:
    """Generate 'Previously on...' recap text from rivalry hooks."""
    if not hooks:
        return "A fresh start — no history, no grudges. Yet."
    lines = ["Previously on Agent Grounds..."]
    for h in hooks:
        a, b = h["pair"]
        if h["narrative"]:
            lines.append(f"{a} vs {b}: {h['narrative'][0]}")
        else:
            lines.append(f"{a} and {b} have met {h['matches']} times.")
    return " ".join(lines)


def _build_pre_match(
    participants: list[dict[str, str]],
    profiles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Generate participant intro cards from profiles."""
    intros: list[dict[str, Any]] = []
    for p in participants:
        emoji = p["emoji"]
        prof = profiles.get(emoji, _DEFAULT_PROFILE)
        intros.append({
            "emoji": emoji,
            "name": p["name"],
            "variant": prof.get("archetype_variant", "Unknown"),
            "traits": prof.get("traits", []),
            "bio": prof.get("bio", ""),
        })
    return {"intros": intros}


def _build_match_commentary(
    commentary: list[dict[str, Any]],
) -> dict[str, Any]:
    """Wrap commentary track for the match section."""
    return {"lines": commentary}


def _build_post_match(
    match_data: dict[str, Any],
    highlights: list[dict[str, Any]],
    season_standings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Post-match: stat diffs, highlight manifest, standings."""
    return {
        "winner": match_data.get("winner"),
        "stat_diffs": _compute_stat_diffs(match_data),
        "highlights": highlights,
        "standings": season_standings,
    }


def _compute_stat_diffs(match_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Compute per-participant stat summaries from match stats."""
    stats = match_data.get("stats", {})
    if not stats:
        return []
    diffs: list[dict[str, Any]] = []
    for emoji, st in stats.items():
        diffs.append({"emoji": emoji, **st})
    return diffs
