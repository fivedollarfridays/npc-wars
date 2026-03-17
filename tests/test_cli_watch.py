"""Tests for the npcwars watch CLI command (T20.2)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _run_main(
    argv: list[str], capsys: pytest.CaptureFixture[str],
) -> tuple[str, str, int]:
    """Run main() and return (stdout, stderr, exit_code)."""
    from npcwars.cli import main

    try:
        main(argv)
        captured = capsys.readouterr()
        return captured.out, captured.err, 0
    except SystemExit as exc:
        captured = capsys.readouterr()
        return captured.out, captured.err, exc.code


# -- Minimal match fixture --------------------------------------------------

def _make_match(tmp_path: Path) -> Path:
    """Write a minimal valid match JSON and return its path."""
    match_data = {
        "players": [
            {"name": "Alpha", "emoji": "A"},
            {"name": "Beta", "emoji": "B"},
        ],
        "grid_size": 5,
        "rounds": [
            {
                "round": 1,
                "storm_border": 0,
                "positions": [
                    {"emoji": "A", "x": 1, "y": 1, "alive": True, "hp": 100, "energy": 5},
                    {"emoji": "B", "x": 3, "y": 3, "alive": True, "hp": 80, "energy": 4},
                ],
                "events": [],
            },
            {
                "round": 2,
                "storm_border": 1,
                "positions": [
                    {"emoji": "A", "x": 2, "y": 2, "alive": True, "hp": 90, "energy": 4},
                    {"emoji": "B", "x": 3, "y": 2, "alive": False, "hp": 0, "energy": 0},
                ],
                "events": [
                    {"type": "kill", "attacker": "A", "victim": "B"},
                ],
            },
        ],
        "winner": "A",
        "duration_rounds": 2,
    }
    filepath = tmp_path / "match_test.json"
    filepath.write_text(json.dumps(match_data), encoding="utf-8")
    return filepath


# -- Cycle 1: Registration and help ----------------------------------------

class TestWatchRegistered:
    """watch subcommand is registered in the CLI."""

    def test_watch_appears_in_help(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        out, _err, code = _run_main(["--help"], capsys)
        assert code == 0
        assert "watch" in out

    def test_watch_help_exits_zero(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        out, _err, code = _run_main(["watch", "--help"], capsys)
        assert code == 0
        assert "--speed" in out
        assert "--no-clear" in out


# -- Cycle 2: Error cases --------------------------------------------------

class TestWatchErrors:
    """Error cases exit non-zero with a message."""

    def test_missing_file_exits_nonzero(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        _out, err, code = _run_main(["watch", "/nonexistent/file.json"], capsys)
        assert code != 0
        assert "not found" in err.lower() or "error" in err.lower()

    def test_invalid_json_exits_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("NOT VALID JSON {{{", encoding="utf-8")
        _out, err, code = _run_main(["watch", str(bad_file)], capsys)
        assert code != 0
        assert "error" in err.lower()


# -- Cycle 3: Successful playback ------------------------------------------

class TestWatchPlayback:
    """watch plays back a match file."""

    def test_watch_plays_match(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        filepath = _make_match(tmp_path)
        out, _err, code = _run_main(
            ["watch", str(filepath), "--speed", "1000", "--no-clear"], capsys,
        )
        assert code == 0
        # Should contain round data rendered by TerminalRenderer
        assert "Round 1" in out or "Round" in out

    def test_watch_shows_winner_banner(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        filepath = _make_match(tmp_path)
        out, _err, code = _run_main(
            ["watch", str(filepath), "--speed", "1000", "--no-clear"], capsys,
        )
        assert code == 0
        assert "WINNER" in out
        assert "Alpha" in out

    def test_watch_renders_all_rounds(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        filepath = _make_match(tmp_path)
        out, _err, code = _run_main(
            ["watch", str(filepath), "--speed", "1000", "--no-clear"], capsys,
        )
        assert code == 0
        # Both rounds should appear
        assert "Round 1" in out
        assert "Round 2" in out
