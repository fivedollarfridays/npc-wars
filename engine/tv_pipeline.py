"""TV pipeline — enrich match_data with commentary, highlights, profiles, rivalries, dossier."""
from __future__ import annotations

import dataclasses
from itertools import combinations
from typing import Any

from data.rivalry_db import compute_rivalry
from engine.commentary import generate_commentary
from engine.highlights import extract_highlights
from engine.personality import profile_bot
from engine.watcher_dossier import build_dossier


def enrich_tv(
    match_data: dict[str, Any],
    *,
    results_dir: str = "results",
    patterns_dir: str = "data/rival_patterns",
) -> None:
    """Append TV keys to *match_data* in place.

    Adds: commentary, highlights, profiles, rivalries, watcher_dossier.
    """
    players = match_data.get("players", [])
    emojis = [p["emoji"] for p in players]

    profiles = _build_profiles(players, results_dir, patterns_dir)
    rivalry_map, rivalry_json = _build_rivalries(emojis, results_dir)
    highlights = extract_highlights(match_data)
    commentary_lines = generate_commentary(match_data, profiles, rivalry_map)
    commentary = [dataclasses.asdict(line) for line in commentary_lines]
    watcher_dossier = _build_dossiers(players, patterns_dir)

    match_data["commentary"] = commentary
    match_data["highlights"] = highlights
    match_data["profiles"] = profiles
    match_data["rivalries"] = rivalry_json
    match_data["watcher_dossier"] = watcher_dossier


def _build_profiles(
    players: list[dict[str, Any]], results_dir: str, patterns_dir: str,
) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for p in players:
        profiles[p["emoji"]] = profile_bot(p["emoji"], results_dir, patterns_dir)
    return profiles


def _build_rivalries(
    emojis: list[str], results_dir: str,
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, dict[str, Any]]]:
    rivalry_map: dict[tuple[str, str], dict[str, Any]] = {}
    rivalry_json: dict[str, dict[str, Any]] = {}
    for a, b in combinations(emojis, 2):
        stats = compute_rivalry(a, b, results_dir)
        rivalry_map[(a, b)] = stats
        rivalry_json[f"{a}:{b}"] = stats
    return rivalry_map, rivalry_json


def _build_dossiers(
    players: list[dict[str, Any]], patterns_dir: str,
) -> dict[str, dict[str, Any]]:
    dossiers: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for p in players:
        author = p.get("author", p["emoji"])
        if author in seen:
            continue
        seen.add(author)
        dossiers[author] = build_dossier(author, patterns_dir, "data/watcher_stats.json")
    return dossiers
