"""Rival progress storage — SQLite table and CRUD functions."""

from __future__ import annotations

import sqlite3

from server.db import _write_lock

WINS_TO_ADVANCE = 2
MAX_RIVAL_TIER = 5


def init_rival_table(conn: sqlite3.Connection) -> None:
    """Create the rival_progress table idempotently."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS rival_progress (
            player_id    TEXT PRIMARY KEY,
            current_tier INTEGER NOT NULL DEFAULT 1,
            attempts     INTEGER NOT NULL DEFAULT 0,
            wins         INTEGER NOT NULL DEFAULT 0
        )
        """
    )


def get_rival_progress(conn: sqlite3.Connection, player_id: str) -> dict | None:
    """Return a rival progress dict or None if not found."""
    row = conn.execute(
        "SELECT * FROM rival_progress WHERE player_id = ?", (player_id,)
    ).fetchone()
    return dict(row) if row else None


def ensure_rival_progress(conn: sqlite3.Connection, player_id: str) -> dict:
    """Insert default progress if missing, then return the row."""
    with _write_lock:
        conn.execute(
            "INSERT OR IGNORE INTO rival_progress (player_id) VALUES (?)",
            (player_id,),
        )
        conn.commit()
    return get_rival_progress(conn, player_id)  # type: ignore[return-value]


def record_rival_attempt(
    conn: sqlite3.Connection, player_id: str, *, won: bool
) -> dict:
    """Record an attempt; advance tier on win threshold."""
    with _write_lock:
        conn.execute(
            "UPDATE rival_progress SET attempts = attempts + 1 WHERE player_id = ?",
            (player_id,),
        )
        if won:
            conn.execute(
                "UPDATE rival_progress SET wins = wins + 1 WHERE player_id = ?",
                (player_id,),
            )
        conn.commit()

    progress = get_rival_progress(conn, player_id)  # type: ignore[arg-type]
    assert progress is not None

    if progress["wins"] >= WINS_TO_ADVANCE and progress["current_tier"] < MAX_RIVAL_TIER:
        with _write_lock:
            conn.execute(
                "UPDATE rival_progress SET current_tier = current_tier + 1, wins = 0 "
                "WHERE player_id = ?",
                (player_id,),
            )
            conn.commit()
        progress = get_rival_progress(conn, player_id)  # type: ignore[arg-type]

    return progress  # type: ignore[return-value]


def get_rival_tier(conn: sqlite3.Connection, player_id: str) -> int:
    """Return the player's current rival tier, defaulting to 1."""
    progress = get_rival_progress(conn, player_id)
    if progress is None:
        return 1
    return progress["current_tier"]
