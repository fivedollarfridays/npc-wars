"""SQLite player registry — players and sessions tables."""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import datetime, timezone


def init_db(db_path: str) -> sqlite3.Connection:
    """Create tables idempotently and return an open connection."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            key       TEXT PRIMARY KEY,
            player_id TEXT NOT NULL REFERENCES players(id),
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bots (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id  TEXT NOT NULL REFERENCES players(id),
            name       TEXT NOT NULL,
            emoji      TEXT NOT NULL,
            source     TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS match_players (
            match_id   INTEGER NOT NULL,
            player_id  TEXT NOT NULL,
            bot_id     INTEGER NOT NULL,
            PRIMARY KEY (match_id, player_id)
        )
        """
    )
    # Cosmetic tables (catalog + inventory)
    from server.cosmetic_db import init_cosmetic_tables

    init_cosmetic_tables(conn)

    # Tournament tables
    from server.tournament_db import init_tournament_table

    init_tournament_table(conn)
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


# ── API Key operations ───────────────────────────────────────────────


def _hash_key(raw_key: str) -> str:
    """Return the SHA-256 hex digest of *raw_key*."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def create_api_key(conn: sqlite3.Connection, player_id: str) -> str:
    """Generate a new API key, store its hash, and return the raw key."""
    key = uuid.uuid4().hex
    key_hash = _hash_key(key)
    created_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO api_keys (key, player_id, created_at) VALUES (?, ?, ?)",
        (key_hash, player_id, created_at),
    )
    conn.commit()
    return key


def get_player_by_api_key(conn: sqlite3.Connection, key: str) -> dict | None:
    """Look up a player by API key (dual-mode: hash first, plaintext fallback).

    New keys are stored as SHA-256 hashes. For migration from old plaintext
    keys, we fall back to a plaintext match and auto-upgrade to hashed.
    """
    key_hash = _hash_key(key)

    # Primary path: match by hash
    row = conn.execute(
        "SELECT p.* FROM players p "
        "JOIN api_keys ak ON ak.player_id = p.id "
        "WHERE ak.key = ?",
        (key_hash,),
    ).fetchone()
    if row:
        return dict(row)

    # Fallback: plaintext match (old keys) — auto-upgrade
    row = conn.execute(
        "SELECT p.* FROM players p "
        "JOIN api_keys ak ON ak.player_id = p.id "
        "WHERE ak.key = ?",
        (key,),
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE api_keys SET key = ? WHERE key = ?", (key_hash, key)
        )
        conn.commit()
        return dict(row)

    return None


# ── Bot operations ───────────────────────────────────────────────────


def store_bot(
    conn: sqlite3.Connection,
    player_id: str,
    name: str,
    emoji: str,
    source: str,
) -> int:
    """Insert a bot and return its id."""
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO bots (player_id, name, emoji, source, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (player_id, name, emoji, source, now, now),
    )
    conn.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def get_bot(conn: sqlite3.Connection, bot_id: int) -> dict | None:
    """Return a bot dict or None if not found."""
    row = conn.execute("SELECT * FROM bots WHERE id = ?", (bot_id,)).fetchone()
    return dict(row) if row else None


def get_player_bots(conn: sqlite3.Connection, player_id: str) -> list[dict]:
    """Return all bots for a player ordered by creation time."""
    rows = conn.execute(
        "SELECT * FROM bots WHERE player_id = ? ORDER BY created_at",
        (player_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ── Match tracking ──────────────────────────────────────────────────


def record_match_player(
    conn: sqlite3.Connection, match_id: int, player_id: str, bot_id: int
) -> None:
    """Record that a player participated in a match with a specific bot."""
    conn.execute(
        "INSERT INTO match_players (match_id, player_id, bot_id) VALUES (?, ?, ?)",
        (match_id, player_id, bot_id),
    )
    conn.commit()


def get_player_matches(
    conn: sqlite3.Connection, player_id: str, limit: int = 20
) -> list[int]:
    """Return recent match IDs for a player, newest first."""
    rows = conn.execute(
        "SELECT match_id FROM match_players WHERE player_id = ? "
        "ORDER BY match_id DESC LIMIT ?",
        (player_id, limit),
    ).fetchall()
    return [row["match_id"] for row in rows]
