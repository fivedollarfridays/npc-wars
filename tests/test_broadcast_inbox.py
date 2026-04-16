"""Tests for engine/broadcast_inbox.py — post-match broadcast inbox hook (T70.2)."""

from __future__ import annotations

import json
import logging
from unittest.mock import patch

import pytest

from engine.broadcast_inbox import write_to_inbox


@pytest.fixture
def match_data():
    return {
        "match_id": 42,
        "winner": "🤖",
        "rounds": [],
        "stats": {},
    }


class TestEnvUnset:
    def test_returns_none_when_env_unset(self, monkeypatch, match_data):
        monkeypatch.delenv("BROADCAST_INBOX_PATH", raising=False)
        assert write_to_inbox(match_data, "killswitch") is None

    def test_returns_none_when_env_empty(self, monkeypatch, match_data):
        monkeypatch.setenv("BROADCAST_INBOX_PATH", "")
        assert write_to_inbox(match_data, "killswitch") is None

    def test_no_file_written_when_env_unset(
        self, monkeypatch, tmp_path, match_data,
    ):
        monkeypatch.delenv("BROADCAST_INBOX_PATH", raising=False)
        write_to_inbox(match_data, "killswitch")
        assert list(tmp_path.iterdir()) == []


class TestWriteWhenEnvSet:
    def test_writes_file_to_inbox(self, monkeypatch, tmp_path, match_data):
        monkeypatch.setenv("BROADCAST_INBOX_PATH", str(tmp_path))
        path = write_to_inbox(match_data, "killswitch")
        assert path is not None
        target = tmp_path / "killswitch" / "42.json"
        assert target.exists()
        assert path == str(target)

    def test_content_matches_match_data(self, monkeypatch, tmp_path, match_data):
        monkeypatch.setenv("BROADCAST_INBOX_PATH", str(tmp_path))
        write_to_inbox(match_data, "killswitch")
        with open(tmp_path / "killswitch" / "42.json") as f:
            loaded = json.load(f)
        assert loaded == match_data

    def test_circuit_game_subdir(self, monkeypatch, tmp_path, match_data):
        monkeypatch.setenv("BROADCAST_INBOX_PATH", str(tmp_path))
        write_to_inbox(match_data, "circuit")
        assert (tmp_path / "circuit" / "42.json").exists()

    def test_different_games_isolated(self, monkeypatch, tmp_path, match_data):
        monkeypatch.setenv("BROADCAST_INBOX_PATH", str(tmp_path))
        write_to_inbox(match_data, "killswitch")
        write_to_inbox({**match_data, "match_id": 7}, "circuit")
        assert (tmp_path / "killswitch" / "42.json").exists()
        assert (tmp_path / "circuit" / "7.json").exists()
        assert not (tmp_path / "killswitch" / "7.json").exists()


class TestAutoCreateDir:
    def test_creates_missing_game_subdir(
        self, monkeypatch, tmp_path, match_data,
    ):
        monkeypatch.setenv("BROADCAST_INBOX_PATH", str(tmp_path))
        assert not (tmp_path / "killswitch").exists()
        write_to_inbox(match_data, "killswitch")
        assert (tmp_path / "killswitch").is_dir()

    def test_creates_nested_inbox_path(
        self, monkeypatch, tmp_path, match_data,
    ):
        nested = tmp_path / "a" / "b" / "inbox"
        monkeypatch.setenv("BROADCAST_INBOX_PATH", str(nested))
        assert not nested.exists()
        write_to_inbox(match_data, "killswitch")
        assert (nested / "killswitch" / "42.json").exists()


class TestIdempotent:
    def test_rewrite_overwrites(self, monkeypatch, tmp_path, match_data):
        monkeypatch.setenv("BROADCAST_INBOX_PATH", str(tmp_path))
        write_to_inbox(match_data, "killswitch")
        updated = {**match_data, "winner": "💀"}
        path = write_to_inbox(updated, "killswitch")
        assert path is not None
        with open(path) as f:
            assert json.load(f)["winner"] == "💀"

    def test_rewrite_returns_same_path(
        self, monkeypatch, tmp_path, match_data,
    ):
        monkeypatch.setenv("BROADCAST_INBOX_PATH", str(tmp_path))
        p1 = write_to_inbox(match_data, "killswitch")
        p2 = write_to_inbox(match_data, "killswitch")
        assert p1 == p2


class TestWriteFailure:
    def test_logs_warning_on_failure(
        self, monkeypatch, tmp_path, match_data, caplog,
    ):
        monkeypatch.setenv("BROADCAST_INBOX_PATH", str(tmp_path))
        with patch(
            "engine.broadcast_inbox.open", side_effect=OSError("disk full"),
        ), caplog.at_level(logging.WARNING):
            result = write_to_inbox(match_data, "killswitch")
        assert result is None
        assert any(
            "broadcast inbox" in rec.message.lower() for rec in caplog.records
        )

    def test_does_not_raise_on_failure(
        self, monkeypatch, tmp_path, match_data,
    ):
        monkeypatch.setenv("BROADCAST_INBOX_PATH", str(tmp_path))
        with patch(
            "engine.broadcast_inbox.open", side_effect=OSError("nope"),
        ):
            write_to_inbox(match_data, "killswitch")

    def test_missing_match_id_logged(self, monkeypatch, tmp_path, caplog):
        monkeypatch.setenv("BROADCAST_INBOX_PATH", str(tmp_path))
        with caplog.at_level(logging.WARNING):
            result = write_to_inbox({"winner": "🤖"}, "killswitch")
        assert result is None
        assert any(
            "match_id" in rec.message.lower() for rec in caplog.records
        )
