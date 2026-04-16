"""Game-agnostic season manager with SQLite storage.

Supports Kill Switch scoring (kills + placement) and Code Circuit scoring
(F1 position points). Tier system: Bronze / Silver / Gold / Diamond.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

__all__ = [
    "init_seasons_tables",
    "create_season",
    "record_result",
    "get_standings",
    "promote_relegate",
]

DEFAULT_TIER_THRESHOLDS: dict[str, float] = {
    "Diamond": 0.10,
    "Gold": 0.30,
    "Silver": 0.60,
}
TIER_ORDER = ("Diamond", "Gold", "Silver", "Bronze")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def init_seasons_tables(conn: sqlite3.Connection) -> None:
    """Create seasons and results tables idempotently."""
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seasons (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT NOT NULL,
            config_json    TEXT NOT NULL DEFAULT '{}',
            scoring_json   TEXT NOT NULL DEFAULT '{}'
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS season_results (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            season_id  INTEGER NOT NULL REFERENCES seasons(id),
            participant TEXT NOT NULL,
            points     INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_season(
    conn: sqlite3.Connection,
    name: str,
    config: dict[str, Any],
    scoring_rules: dict[str, Any],
) -> int:
    """Create a new season and return its id."""
    cursor = conn.execute(
        "INSERT INTO seasons (name, config_json, scoring_json) VALUES (?, ?, ?)",
        (name, json.dumps(config), json.dumps(scoring_rules)),
    )
    conn.commit()
    return cursor.lastrowid  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _score_result(scoring: dict[str, Any], match_data: dict[str, Any]) -> int:
    """Compute points for a single match result using game-specific rules."""
    stype = scoring.get("type", "")
    if stype == "kill_switch":
        kill_pts = scoring.get("kill_points", 0)
        placement_map = scoring.get("placement_points", {})
        kills = match_data.get("kills", 0)
        placement = match_data.get("placement", 0)
        return kills * kill_pts + placement_map.get(str(placement), placement_map.get(placement, 0))
    if stype == "code_circuit":
        pos_map = scoring.get("position_points", {})
        position = match_data.get("position", 0)
        return pos_map.get(str(position), pos_map.get(position, 0))
    return 0


# ---------------------------------------------------------------------------
# Record
# ---------------------------------------------------------------------------

def record_result(
    season_id: int,
    match_data: dict[str, Any],
    *,
    conn: sqlite3.Connection,
) -> None:
    """Record a match result, adding scored points to the participant."""
    row = conn.execute(
        "SELECT scoring_json FROM seasons WHERE id = ?", (season_id,)
    ).fetchone()
    if row is None:
        msg = f"Season {season_id} not found"
        raise ValueError(msg)
    scoring = json.loads(row["scoring_json"])
    participant = match_data["participant"]
    points = _score_result(scoring, match_data)
    conn.execute(
        "INSERT INTO season_results (season_id, participant, points) VALUES (?, ?, ?)",
        (season_id, participant, points),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Standings
# ---------------------------------------------------------------------------

def _assign_tiers(
    standings: list[dict[str, Any]], thresholds: dict[str, float]
) -> None:
    """Mutate standings in-place to add tier assignments."""
    n = len(standings)
    for i, entry in enumerate(standings):
        rank_pct = (i + 1) / n if n else 1.0
        entry["tier"] = "Bronze"
        for tier in ("Diamond", "Gold", "Silver"):
            if rank_pct <= thresholds.get(tier, DEFAULT_TIER_THRESHOLDS.get(tier, 1.0)):
                entry["tier"] = tier
                break


def get_standings(
    season_id: int, *, conn: sqlite3.Connection
) -> list[dict[str, Any]]:
    """Return sorted standings with tier assignments."""
    rows = conn.execute(
        """
        SELECT participant, SUM(points) as points
        FROM season_results
        WHERE season_id = ?
        GROUP BY participant
        ORDER BY points DESC
        """,
        (season_id,),
    ).fetchall()
    standings = [{"participant": r["participant"], "points": r["points"]} for r in rows]

    config_row = conn.execute(
        "SELECT config_json FROM seasons WHERE id = ?", (season_id,)
    ).fetchone()
    config = json.loads(config_row["config_json"]) if config_row else {}
    thresholds = config.get("tier_thresholds", DEFAULT_TIER_THRESHOLDS)
    _assign_tiers(standings, thresholds)
    return standings


# ---------------------------------------------------------------------------
# Promotion / Relegation
# ---------------------------------------------------------------------------

def promote_relegate(
    season_id: int, *, conn: sqlite3.Connection
) -> list[dict[str, Any]]:
    """Compute promotion/relegation changes at season end.

    Returns list of ``{"participant", "from_tier", "to_tier", "action"}`` dicts.
    """
    standings = get_standings(season_id, conn=conn)
    if len(standings) <= 1:
        return []

    config_row = conn.execute(
        "SELECT config_json FROM seasons WHERE id = ?", (season_id,)
    ).fetchone()
    config = json.loads(config_row["config_json"]) if config_row else {}
    promote_n = config.get("promote_top_n", 1)
    relegate_n = config.get("relegate_bottom_n", 1)

    # Group by tier
    tiers: dict[str, list[dict[str, Any]]] = {}
    for entry in standings:
        tiers.setdefault(entry["tier"], []).append(entry)

    changes: list[dict[str, Any]] = []
    for idx, tier in enumerate(TIER_ORDER):
        members = tiers.get(tier, [])
        if not members:
            continue
        higher = TIER_ORDER[idx - 1] if idx > 0 else None
        lower = TIER_ORDER[idx + 1] if idx < len(TIER_ORDER) - 1 else None

        # Promote top N (except already Diamond)
        if higher:
            for entry in members[:promote_n]:
                changes.append({
                    "participant": entry["participant"],
                    "from_tier": tier,
                    "to_tier": higher,
                    "action": "promote",
                })
        # Relegate bottom N (except already Bronze)
        if lower:
            for entry in members[-relegate_n:]:
                changes.append({
                    "participant": entry["participant"],
                    "from_tier": tier,
                    "to_tier": lower,
                    "action": "relegate",
                })
    return changes
