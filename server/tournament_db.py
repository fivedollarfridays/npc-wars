"""Tournament storage — SQLite table and CRUD functions."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from server.db import _write_lock


def init_tournament_table(conn: sqlite3.Connection) -> None:
    """Create the tournaments table idempotently."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tournaments (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL,
            size         INTEGER NOT NULL,
            status       TEXT NOT NULL DEFAULT 'open',
            bracket_json TEXT NOT NULL DEFAULT '{}',
            map_name     TEXT DEFAULT 'arena',
            created_at   TEXT NOT NULL,
            winner       TEXT
        )
        """
    )


def create_tournament(
    conn: sqlite3.Connection, name: str, size: int, map_name: str = "arena"
) -> int:
    """Insert a tournament and return its id."""
    created_at = datetime.now(timezone.utc).isoformat()
    with _write_lock:
        cursor = conn.execute(
            "INSERT INTO tournaments (name, size, map_name, created_at) VALUES (?, ?, ?, ?)",
            (name, size, map_name, created_at),
        )
        conn.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def get_tournament(conn: sqlite3.Connection, tournament_id: int) -> dict | None:
    """Return a tournament dict or None if not found."""
    row = conn.execute(
        "SELECT * FROM tournaments WHERE id = ?", (tournament_id,)
    ).fetchone()
    return dict(row) if row else None


def update_tournament(
    conn: sqlite3.Connection,
    tournament_id: int,
    bracket_json: str,
    status: str,
    winner: str | None,
) -> None:
    """Update bracket JSON, status, and winner for a tournament."""
    with _write_lock:
        conn.execute(
            "UPDATE tournaments SET bracket_json = ?, status = ?, winner = ? WHERE id = ?",
            (bracket_json, status, winner, tournament_id),
        )
        conn.commit()


def list_tournaments(
    conn: sqlite3.Connection, limit: int = 20
) -> list[dict]:
    """Return recent tournaments, newest first."""
    rows = conn.execute(
        "SELECT * FROM tournaments ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]
