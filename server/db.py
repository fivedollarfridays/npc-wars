"""SQLite player registry — players and sessions tables."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


def init_db(db_path: str) -> sqlite3.Connection:
    """Create tables idempotently and return an open connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS players (
            id      TEXT PRIMARY KEY,
            name    TEXT NOT NULL,
            created TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token     TEXT PRIMARY KEY,
            player_id TEXT NOT NULL REFERENCES players(id),
            expires   TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


# ── Player CRUD ──────────────────────────────────────────────────────


def create_player(conn: sqlite3.Connection, player_id: str, name: str) -> dict:
    """Insert a new player and return its data as a dict."""
    created = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO players (id, name, created) VALUES (?, ?, ?)",
        (player_id, name, created),
    )
    conn.commit()
    return {"id": player_id, "name": name, "created": created}


def get_player(conn: sqlite3.Connection, player_id: str) -> dict | None:
    """Return a player dict or None if not found."""
    row = conn.execute(
        "SELECT * FROM players WHERE id = ?", (player_id,)
    ).fetchone()
    return dict(row) if row else None


def list_players(conn: sqlite3.Connection) -> list[dict]:
    """Return all players ordered by creation time."""
    rows = conn.execute("SELECT * FROM players ORDER BY created").fetchall()
    return [dict(r) for r in rows]


# ── Session operations ───────────────────────────────────────────────


def create_session(
    conn: sqlite3.Connection, token: str, player_id: str, expires: str
) -> dict:
    """Insert a new session and return its data as a dict."""
    conn.execute(
        "INSERT INTO sessions (token, player_id, expires) VALUES (?, ?, ?)",
        (token, player_id, expires),
    )
    conn.commit()
    return {"token": token, "player_id": player_id, "expires": expires}


def get_session(conn: sqlite3.Connection, token: str) -> dict | None:
    """Return a session dict or None if not found."""
    row = conn.execute(
        "SELECT * FROM sessions WHERE token = ?", (token,)
    ).fetchone()
    return dict(row) if row else None


def expire_session(conn: sqlite3.Connection, token: str) -> bool:
    """Delete a session. Return True if a row was removed."""
    cursor = conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    return cursor.rowcount > 0
