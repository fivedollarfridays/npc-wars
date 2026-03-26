"""Tests for T51.1: SQLite write lock — verify _write_lock exists and works."""

from __future__ import annotations

import sqlite3
import threading
import time

from server.db import _write_lock, create_player, get_player, init_db


def _make_conn() -> sqlite3.Connection:
    """Return a fresh in-memory DB connection with all tables."""
    return init_db(":memory:")


# ── Cycle 1: Lock existence ───────────────────────────────────────────


def test_write_lock_exists() -> None:
    """_write_lock should be a threading.Lock instance."""
    assert isinstance(_write_lock, type(threading.Lock()))


# ── Cycle 2: Concurrent writes ───────────────────────────────────────


def test_concurrent_writes_no_corruption() -> None:
    """Spawn 10 threads each creating a player — all should succeed."""
    conn = _make_conn()
    errors: list[Exception] = []

    def _create(idx: int) -> None:
        try:
            create_player(conn, f"p{idx}", f"Player {idx}")
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_create, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"Unexpected errors: {errors}"

    # All 10 players should exist
    for i in range(10):
        assert get_player(conn, f"p{i}") is not None, f"Player p{i} missing"


# ── Cycle 3: Reads don't block on write lock ─────────────────────────


def test_reads_dont_block_on_write_lock() -> None:
    """While the write lock is held, reads should still return quickly."""
    conn = _make_conn()
    create_player(conn, "existing", "Existing Player")

    read_result: dict | None = None
    read_duration: float = 0.0

    def _slow_hold_lock() -> None:
        with _write_lock:
            time.sleep(0.3)

    def _quick_read() -> None:
        nonlocal read_result, read_duration
        start = time.monotonic()
        read_result = get_player(conn, "existing")
        read_duration = time.monotonic() - start

    writer = threading.Thread(target=_slow_hold_lock)
    writer.start()
    time.sleep(0.05)  # let the writer acquire the lock

    reader = threading.Thread(target=_quick_read)
    reader.start()
    reader.join()
    writer.join()

    assert read_result is not None, "Read should return the player"
    assert read_result["name"] == "Existing Player"
    # Read should complete much faster than the 0.3s lock hold
    assert read_duration < 0.25, f"Read took {read_duration:.3f}s — blocked on write lock?"
