"""Cosmetic inventory persistence — SQLite tables and CRUD operations."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from server.cosmetics import COSMETIC_CATALOG


def init_cosmetic_tables(conn: sqlite3.Connection) -> None:
    """Create cosmetic-related tables idempotently."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cosmetic_inventory (
            player_id    TEXT NOT NULL,
            cosmetic_id  TEXT NOT NULL,
            equipped     INTEGER NOT NULL DEFAULT 0,
            purchased_at TEXT NOT NULL,
            PRIMARY KEY (player_id, cosmetic_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS player_coins (
            player_id TEXT PRIMARY KEY,
            balance   INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()


# ── Coin operations ─────────────────────────────────────────────────


def get_coin_balance(conn: sqlite3.Connection, player_id: str) -> int:
    """Return the coin balance for a player (0 if no row)."""
    row = conn.execute(
        "SELECT balance FROM player_coins WHERE player_id = ?",
        (player_id,),
    ).fetchone()
    return int(row["balance"]) if row else 0


def award_coins(conn: sqlite3.Connection, player_id: str, amount: int) -> None:
    """Add coins to a player's balance (upsert)."""
    conn.execute(
        """
        INSERT INTO player_coins (player_id, balance) VALUES (?, ?)
        ON CONFLICT(player_id) DO UPDATE SET balance = balance + excluded.balance
        """,
        (player_id, amount),
    )
    conn.commit()


# ── Purchase ────────────────────────────────────────────────────────


def purchase_cosmetic(
    conn: sqlite3.Connection, player_id: str, cosmetic_id: str
) -> tuple[bool, str]:
    """Buy a cosmetic. Returns (success, message)."""
    if cosmetic_id not in COSMETIC_CATALOG:
        return False, "Unknown cosmetic item"

    item = COSMETIC_CATALOG[cosmetic_id]

    # Already owned?
    existing = conn.execute(
        "SELECT 1 FROM cosmetic_inventory WHERE player_id = ? AND cosmetic_id = ?",
        (player_id, cosmetic_id),
    ).fetchone()
    if existing:
        return False, "Already owned"

    balance = get_coin_balance(conn, player_id)
    if balance < item["price"]:
        return False, "Insufficient coins"

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE player_coins SET balance = balance - ? WHERE player_id = ?",
        (item["price"], player_id),
    )
    conn.execute(
        "INSERT INTO cosmetic_inventory (player_id, cosmetic_id, purchased_at) VALUES (?, ?, ?)",
        (player_id, cosmetic_id, now),
    )
    conn.commit()
    return True, "Purchased"


# ── Inventory ───────────────────────────────────────────────────────


def get_player_inventory(conn: sqlite3.Connection, player_id: str) -> list[dict]:
    """Return all cosmetics owned by a player."""
    rows = conn.execute(
        "SELECT cosmetic_id, equipped, purchased_at FROM cosmetic_inventory WHERE player_id = ?",
        (player_id,),
    ).fetchall()
    result = []
    for row in rows:
        cid = row["cosmetic_id"]
        catalog_data = COSMETIC_CATALOG.get(cid, {})
        result.append({
            "id": cid,
            "equipped": bool(row["equipped"]),
            "purchased_at": row["purchased_at"],
            **catalog_data,
        })
    return result


# ── Equip / Unequip ─────────────────────────────────────────────────


def equip_cosmetic(conn: sqlite3.Connection, player_id: str, cosmetic_id: str) -> bool:
    """Equip a cosmetic. Unequips any other of the same type. Returns success."""
    if cosmetic_id not in COSMETIC_CATALOG:
        return False

    owned = conn.execute(
        "SELECT 1 FROM cosmetic_inventory WHERE player_id = ? AND cosmetic_id = ?",
        (player_id, cosmetic_id),
    ).fetchone()
    if not owned:
        return False

    cosmetic_type = COSMETIC_CATALOG[cosmetic_id]["type"]

    # Unequip all of the same type for this player
    same_type_ids = [
        cid for cid, item in COSMETIC_CATALOG.items() if item["type"] == cosmetic_type
    ]
    placeholders = ",".join("?" for _ in same_type_ids)
    conn.execute(
        f"UPDATE cosmetic_inventory SET equipped = 0 "  # noqa: S608
        f"WHERE player_id = ? AND cosmetic_id IN ({placeholders})",
        [player_id, *same_type_ids],
    )

    conn.execute(
        "UPDATE cosmetic_inventory SET equipped = 1 WHERE player_id = ? AND cosmetic_id = ?",
        (player_id, cosmetic_id),
    )
    conn.commit()
    return True


def unequip_cosmetic(conn: sqlite3.Connection, player_id: str, cosmetic_id: str) -> bool:
    """Unequip a cosmetic. Returns True if it was equipped."""
    cursor = conn.execute(
        "UPDATE cosmetic_inventory SET equipped = 0 "
        "WHERE player_id = ? AND cosmetic_id = ? AND equipped = 1",
        (player_id, cosmetic_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def get_equipped_cosmetics(conn: sqlite3.Connection, player_id: str) -> dict[str, dict]:
    """Return equipped cosmetics as {type: cosmetic_data}."""
    rows = conn.execute(
        "SELECT cosmetic_id FROM cosmetic_inventory WHERE player_id = ? AND equipped = 1",
        (player_id,),
    ).fetchall()
    result: dict[str, dict] = {}
    for row in rows:
        cid = row["cosmetic_id"]
        item = COSMETIC_CATALOG.get(cid)
        if item:
            result[item["type"]] = {"id": cid, **item}
    return result
