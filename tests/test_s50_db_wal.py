"""Tests for T50.4: .env gitignore + SQLite WAL mode."""

import os
import tempfile
from pathlib import Path

from server.db import init_db


def test_gitignore_has_env_pattern():
    """Ensure .gitignore excludes .env files."""
    gitignore = Path(".gitignore").read_text()
    assert ".env" in gitignore


def test_gitignore_has_env_wildcard():
    """Ensure .gitignore excludes .env.* files (e.g. .env.local)."""
    gitignore = Path(".gitignore").read_text()
    assert ".env.*" in gitignore


def test_db_wal_mode():
    """Ensure WAL journal mode is enabled after init_db."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        conn = init_db(db_path)
        result = conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0] == "wal"
        conn.close()
    finally:
        for ext in ["", "-wal", "-shm"]:
            try:
                os.unlink(db_path + ext)
            except FileNotFoundError:
                pass
