"""Delegated player identity storage — opaque ref → player binding (UP-2).

The PSC relay authenticates with a single provisioned service key and names
the acting player with an opaque ``X-Player-Ref`` token.  Refs are stored as
SHA-256 hashes only: the plaintext token never lands in the database, logs or
any rendered surface, and it is never usable as a credential on its own.
"""

from __future__ import annotations

import hashlib
import sqlite3
import uuid

from datetime import datetime, timezone

from server.db import _write_lock, create_player, get_player

_REF_TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS player_refs (
        ref_hash   TEXT PRIMARY KEY,
        player_id  TEXT NOT NULL REFERENCES players(id),
        created_at TEXT NOT NULL
    )
"""


def init_player_ref_table(conn: sqlite3.Connection) -> None:
    """Create the player_refs table idempotently."""
    conn.execute(_REF_TABLE_DDL)


def _hash_ref(ref: str) -> str:
    """Return the SHA-256 hex digest of an opaque player ref."""
    return hashlib.sha256(ref.encode()).hexdigest()


def get_player_by_ref(conn: sqlite3.Connection, ref: str) -> dict | None:
    """Return the player bound to *ref*, or None if the ref is unknown."""
    row = conn.execute(
        "SELECT p.* FROM players p "
        "JOIN player_refs pr ON pr.player_id = p.id "
        "WHERE pr.ref_hash = ?",
        (_hash_ref(ref),),
    ).fetchone()
    return dict(row) if row else None


def bind_player_ref(conn: sqlite3.Connection, ref: str, player_id: str) -> None:
    """Bind *ref* to *player_id*.  First binding wins; later ones are ignored."""
    created_at = datetime.now(timezone.utc).isoformat()
    with _write_lock:
        conn.execute(
            "INSERT OR IGNORE INTO player_refs (ref_hash, player_id, created_at) "
            "VALUES (?, ?, ?)",
            (_hash_ref(ref), player_id, created_at),
        )
        conn.commit()


def resolve_player_by_ref(conn: sqlite3.Connection, ref: str) -> dict:
    """Return the player bound to *ref*, creating one on first sight.

    Stable: the same ref always resolves to the same player.  The generated
    display name is derived from a fresh UUID, never from the ref itself.
    """
    existing = get_player_by_ref(conn, ref)
    if existing:
        return existing

    player_id = uuid.uuid4().hex
    create_player(conn, player_id, f"player_{player_id[:8]}")
    bind_player_ref(conn, ref, player_id)
    # Re-read so a concurrent binding for the same ref wins consistently.
    return get_player_by_ref(conn, ref) or get_player(conn, player_id) or {}
