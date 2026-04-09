"""Code Circuit rivalry tracker — position battle history between car pairs.

Pure functions. Computes overtake/defend rates, gap statistics,
championship points head-to-head, and rivalry score with narrative hooks.
"""

from __future__ import annotations

from typing import Any

__all__ = ["compute_rivalry"]


def compute_rivalry(
    car_a: str, car_b: str, race_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute rivalry stats between two cars from race history.

    Returns dict with: races, overtakes, defends, laps_battling,
    points, avg_gap, rivalry_score (0-100), narrative_hooks.
    """
    ov_a = ov_b = def_a = def_b = laps = pts_a = pts_b = races = 0
    gaps: list[int] = []

    for race in race_history:
        if car_a not in race.get("cars", []) or car_b not in race.get("cars", []):
            continue
        races += 1
        t = _tally_race(race, car_a, car_b)
        ov_a += t["ov_a"]
        ov_b += t["ov_b"]
        def_a += t["def_a"]
        def_b += t["def_b"]
        laps += t["laps"]
        pts_a += t["pts_a"]
        pts_b += t["pts_b"]
        if t["gap"] is not None:
            gaps.append(t["gap"])

    avg_gap = sum(gaps) / len(gaps) if gaps else 0.0
    score = _rivalry_score(races, ov_a + ov_b, laps, avg_gap)
    hooks = _narrative_hooks(car_a, car_b, races, ov_a, ov_b, def_a, def_b, laps, pts_a, pts_b, avg_gap)

    return {
        "car_a": car_a, "car_b": car_b, "races": races,
        "overtakes_a": ov_a, "overtakes_b": ov_b,
        "defends_a": def_a, "defends_b": def_b,
        "laps_battling": laps,
        "points_a": pts_a, "points_b": pts_b,
        "avg_gap": round(avg_gap, 2),
        "rivalry_score": score,
        "narrative_hooks": hooks,
    }


def _tally_race(race: dict[str, Any], car_a: str, car_b: str) -> dict[str, Any]:
    """Extract pair-specific stats from a single race."""
    ov_a = ov_b = def_a = def_b = 0
    for ov in race.get("overtakes", []):
        if ov["overtaker"] == car_a and ov["defender"] == car_b:
            ov_a += 1
        elif ov["overtaker"] == car_b and ov["defender"] == car_a:
            ov_b += 1
    for d in race.get("defends", []):
        if d["defender"] == car_a and d["attacker"] == car_b:
            def_a += 1
        elif d["defender"] == car_b and d["attacker"] == car_a:
            def_b += 1
    champ = race.get("championship_points", {})
    finish = race.get("finish", {})
    gap = abs(finish[car_a] - finish[car_b]) if car_a in finish and car_b in finish else None
    return {
        "ov_a": ov_a, "ov_b": ov_b, "def_a": def_a, "def_b": def_b,
        "laps": race.get("laps_battling", 0),
        "pts_a": champ.get(car_a, 0), "pts_b": champ.get(car_b, 0),
        "gap": gap,
    }


def _rivalry_score(races: int, total_overtakes: int, laps: int, avg_gap: float) -> int:
    """Compute 0-100 score reflecting how competitive the rivalry is."""
    if races == 0:
        return 0
    overtake_factor = min(total_overtakes / races, 5.0) / 5.0  # 0-1
    battle_factor = min(laps / (races * 30), 1.0)  # 0-1, 30 laps/race norm
    closeness = max(1.0 - avg_gap / 10.0, 0.0)  # 0-1, gap>10 = not close
    volume = min(races / 5.0, 1.0)  # 0-1, 5+ races = full weight
    raw = (overtake_factor * 35 + battle_factor * 25 + closeness * 25 + volume * 15)
    return min(round(raw), 100)


def _narrative_hooks(
    car_a: str, car_b: str, races: int,
    ov_a: int, ov_b: int, def_a: int, def_b: int,
    laps: int, pts_a: int, pts_b: int, avg_gap: float,
) -> list[str]:
    """Generate narrative hooks for commentary."""
    hooks: list[str] = []
    if races == 0:
        return hooks
    total_ov = ov_a + ov_b
    if total_ov >= 3 * races:
        hooks.append(f"{car_a} and {car_b} trade paint every race")
    elif total_ov >= races:
        hooks.append(f"Regular overtake battles between {car_a} and {car_b}")
    if laps / races >= 15:
        hooks.append("Wheel-to-wheel for long stretches")
    if avg_gap <= 2.0:
        hooks.append("Almost always finish within touching distance")
    if abs(pts_a - pts_b) <= 10 and pts_a + pts_b > 0:
        hooks.append("Championship battle is razor-thin")
    if def_a + def_b >= races:
        hooks.append("Defensive masterclass on both sides")
    leader = car_a if ov_a > ov_b * 2 and ov_a >= 3 else (car_b if ov_b > ov_a * 2 and ov_b >= 3 else None)
    if leader:
        hooks.append(f"{leader} owns the overtaking battle")
    return hooks
