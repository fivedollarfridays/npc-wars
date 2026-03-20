"""SQLite persistence for player profiles (XP, level, match stats).

Engine-layer module — no server dependency.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from engine.levels import level_from_xp


_SCHEMA = """\
CREATE TABLE IF NOT EXISTS profiles (
    name        TEXT PRIMARY KEY,
    total_xp    INTEGER NOT NULL DEFAULT 0,
    level       INTEGER NOT NULL DEFAULT 1,
    matches     INTEGER NOT NULL DEFAULT 0,
    wins        INTEGER NOT NULL DEFAULT 0,
    kills       INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""

DEFAULT_DB_PATH = "data/profiles.db"


def init_profile_db(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create the profiles table idempotently and return an open connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def _now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    """Convert a sqlite3.Row to a plain dict, or None."""
    if row is None:
        return None
    return dict(row)


def get_or_create_profile(conn: sqlite3.Connection, name: str) -> dict[str, Any]:
    """Return existing profile or create a new one with defaults."""
    row = conn.execute(
        "SELECT * FROM profiles WHERE name = ?", (name,)
    ).fetchone()
    if row is not None:
        return dict(row)
    now = _now_iso()
    conn.execute(
        "INSERT INTO profiles (name, total_xp, level, matches, wins, kills, created_at, updated_at) "
        "VALUES (?, 0, 1, 0, 0, 0, ?, ?)",
        (name, now, now),
    )
    conn.commit()
    return {
        "name": name, "total_xp": 0, "level": 1,
        "matches": 0, "wins": 0, "kills": 0,
        "created_at": now, "updated_at": now,
    }


def get_profile(conn: sqlite3.Connection, name: str) -> dict[str, Any] | None:
    """Look up a profile by name. Returns None if not found."""
    row = conn.execute(
        "SELECT * FROM profiles WHERE name = ?", (name,)
    ).fetchone()
    return _row_to_dict(row)


def update_profile(
    conn: sqlite3.Connection,
    name: str,
    xp_earned: int,
    kills: int,
    won: bool,
) -> dict[str, Any]:
    """Add XP, increment stats, recalculate level. Upserts if needed."""
    profile = get_or_create_profile(conn, name)
    new_xp = profile["total_xp"] + xp_earned
    new_level = level_from_xp(new_xp)
    new_matches = profile["matches"] + 1
    new_wins = profile["wins"] + (1 if won else 0)
    new_kills = profile["kills"] + kills
    now = _now_iso()
    conn.execute(
        "UPDATE profiles SET total_xp=?, level=?, matches=?, wins=?, kills=?, updated_at=? "
        "WHERE name=?",
        (new_xp, new_level, new_matches, new_wins, new_kills, now, name),
    )
    conn.commit()
    return {
        "name": name, "total_xp": new_xp, "level": new_level,
        "matches": new_matches, "wins": new_wins, "kills": new_kills,
        "created_at": profile["created_at"], "updated_at": now,
    }


def list_profiles(
    conn: sqlite3.Connection,
    order_by: str = "level",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Return sorted profiles. order_by must be a valid column name."""
    _ORDER_QUERIES = {
        "level": "SELECT * FROM profiles ORDER BY level DESC LIMIT ?",
        "total_xp": "SELECT * FROM profiles ORDER BY total_xp DESC LIMIT ?",
        "matches": "SELECT * FROM profiles ORDER BY matches DESC LIMIT ?",
        "wins": "SELECT * FROM profiles ORDER BY wins DESC LIMIT ?",
        "kills": "SELECT * FROM profiles ORDER BY kills DESC LIMIT ?",
        "name": "SELECT * FROM profiles ORDER BY name DESC LIMIT ?",
    }
    query = _ORDER_QUERIES.get(order_by, _ORDER_QUERIES["level"])
    rows = conn.execute(query, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_leaderboard(
    conn: sqlite3.Connection,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Top profiles by level DESC, total_xp DESC."""
    rows = conn.execute(
        "SELECT * FROM profiles ORDER BY level DESC, total_xp DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
