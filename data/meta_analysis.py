"""Meta analysis: aggregate equipment loadouts and stat archetypes across matches.

Computes win rates per weapon/armor/accessory, detects dominant strategies,
and produces a meta report with top builds, counter picks, and trends.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

__all__ = ["generate_meta_report"]

_MIN_MATCHES_DOMINANT = 5
_DOMINANT_WIN_RATE = 0.60


def _load_matches(results_dir: str) -> list[dict[str, Any]]:
    """Load all match JSON files from a directory."""
    path = Path(results_dir)
    matches = []
    for f in sorted(path.glob("match_*.json")):
        with open(f) as fh:
            matches.append(json.load(fh))
    return matches


def _extract_entries(matches: list[dict]) -> list[dict]:
    """Extract per-player entries with equipment from all matches."""
    entries = []
    for match in matches:
        winner = match["winner"]
        for emoji, stats in match["stats"].items():
            equip = stats.get("equipment")
            if not equip:
                continue
            entries.append({
                "emoji": emoji,
                "won": emoji == winner,
                "weapon": equip["weapon"],
                "armor": equip["armor"],
                "accessories": equip.get("accessories", []),
                "archetype": stats.get("archetype", "Unknown"),
                "match_id": match["match_id"],
            })
    return entries


def _win_rates(entries: list[dict], key: str) -> dict[str, dict]:
    """Compute win rates grouped by a key field."""
    buckets: dict[str, dict] = defaultdict(lambda: {"wins": 0, "matches": 0})
    for e in entries:
        val = e[key]
        buckets[val]["matches"] += 1
        if e["won"]:
            buckets[val]["wins"] += 1
    for v in buckets.values():
        v["win_rate"] = v["wins"] / v["matches"] if v["matches"] else 0.0
    return dict(buckets)


def _accessory_win_rates(entries: list[dict]) -> dict[str, dict]:
    """Compute win rates per individual accessory."""
    buckets: dict[str, dict] = defaultdict(lambda: {"wins": 0, "matches": 0})
    for e in entries:
        for acc in e["accessories"]:
            buckets[acc]["matches"] += 1
            if e["won"]:
                buckets[acc]["wins"] += 1
    for v in buckets.values():
        v["win_rate"] = v["wins"] / v["matches"] if v["matches"] else 0.0
    return dict(buckets)


def _find_dominant(win_rate_dicts: list[tuple[str, dict]]) -> list[dict]:
    """Find items with >60% win rate and >=5 matches across categories."""
    dominant = []
    for category, rates in win_rate_dicts:
        for name, data in rates.items():
            if data["matches"] >= _MIN_MATCHES_DOMINANT and data["win_rate"] > _DOMINANT_WIN_RATE:
                dominant.append({
                    "category": category, "name": name,
                    "win_rate": data["win_rate"], "matches": data["matches"],
                })
    dominant.sort(key=lambda d: d["win_rate"], reverse=True)
    return dominant


def _top_builds(entries: list[dict], limit: int = 5) -> list[dict]:
    """Rank weapon+armor combos by win count."""
    builds: dict[tuple, dict] = defaultdict(lambda: {"wins": 0, "matches": 0})
    for e in entries:
        key = (e["weapon"], e["armor"])
        builds[key]["matches"] += 1
        if e["won"]:
            builds[key]["wins"] += 1
    ranked = []
    for (weapon, armor), data in builds.items():
        data["win_rate"] = data["wins"] / data["matches"] if data["matches"] else 0.0
        ranked.append({"weapon": weapon, "armor": armor, **data})
    ranked.sort(key=lambda b: (b["wins"], b["win_rate"]), reverse=True)
    return ranked[:limit]


def _counter_picks(entries: list[dict], dominant: list[dict], limit: int = 3) -> list[dict]:
    """Find builds that beat dominant strategies."""
    if not dominant:
        return []
    dom_weapons = {d["name"] for d in dominant if d["category"] == "weapon"}
    # Track which builds beat dominant weapons
    counters: dict[tuple, dict] = defaultdict(lambda: {"wins_vs_dominant": 0, "matches": 0})
    # Group entries by match_id
    by_match: dict[int, list[dict]] = defaultdict(list)
    for e in entries:
        by_match[e["match_id"]].append(e)
    for match_entries in by_match.values():
        winners = [e for e in match_entries if e["won"]]
        losers = [e for e in match_entries if not e["won"]]
        for w in winners:
            if w["weapon"] in dom_weapons:
                continue
            for lo in losers:
                if lo["weapon"] in dom_weapons:
                    key = (w["weapon"], w["armor"])
                    counters[key]["wins_vs_dominant"] += 1
                    counters[key]["matches"] += 1
    ranked = [{"weapon": k[0], "armor": k[1], **v} for k, v in counters.items()]
    ranked.sort(key=lambda c: c["wins_vs_dominant"], reverse=True)
    return ranked[:limit]


def _meta_trend(entries: list[dict]) -> dict[str, Any]:
    """Compute rising/falling strategies by comparing recent vs overall."""
    if not entries:
        return {"rising": [], "falling": []}
    match_ids = sorted({e["match_id"] for e in entries})
    midpoint = match_ids[len(match_ids) // 2] if len(match_ids) > 1 else match_ids[0]
    recent = [e for e in entries if e["match_id"] >= midpoint]
    overall_rates = _win_rates(entries, "weapon")
    recent_rates = _win_rates(recent, "weapon")
    rising, falling = [], []
    for weapon, overall in overall_rates.items():
        rec = recent_rates.get(weapon, {"win_rate": 0.0})
        delta = rec["win_rate"] - overall["win_rate"]
        if delta > 0.05:
            rising.append({"weapon": weapon, "delta": round(delta, 3)})
        elif delta < -0.05:
            falling.append({"weapon": weapon, "delta": round(delta, 3)})
    rising.sort(key=lambda r: r["delta"], reverse=True)
    falling.sort(key=lambda r: r["delta"])
    return {"rising": rising, "falling": falling}


def generate_meta_report(results_dir: str) -> dict[str, Any]:
    """Generate a meta analysis report from match results.

    Returns dict with: weapon_win_rates, armor_win_rates, accessory_win_rates,
    archetype_win_rates, dominant_strategies, top_builds, counter_picks, meta_trend.
    """
    matches = _load_matches(results_dir)
    entries = _extract_entries(matches)
    weapon_wr = _win_rates(entries, "weapon")
    armor_wr = _win_rates(entries, "armor")
    accessory_wr = _accessory_win_rates(entries)
    archetype_wr = _win_rates(entries, "archetype")
    dominant = _find_dominant([
        ("weapon", weapon_wr), ("armor", armor_wr), ("accessory", accessory_wr),
    ])
    return {
        "weapon_win_rates": weapon_wr,
        "armor_win_rates": armor_wr,
        "accessory_win_rates": accessory_wr,
        "archetype_win_rates": archetype_wr,
        "dominant_strategies": dominant,
        "top_builds": _top_builds(entries),
        "counter_picks": _counter_picks(entries, dominant),
        "meta_trend": _meta_trend(entries),
    }
