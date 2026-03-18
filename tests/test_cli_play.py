"""Tests for the npcwars play CLI command (T20.3)."""
from __future__ import annotations

from pathlib import Path

import pytest


def _run_main(
    argv: list[str], capsys: pytest.CaptureFixture[str],
) -> tuple[str, str, int]:
    """Run main() and return (stdout, stderr, exit_code)."""
    from agentgrounds.wars.cli import main

    try:
        main(argv)
        captured = capsys.readouterr()
        return captured.out, captured.err, 0
    except SystemExit as exc:
        captured = capsys.readouterr()
        return captured.out, captured.err, exc.code


# -- Minimal bot sources for testing ------------------------------------------

_BOT_A = """\
BOT_NAME = "AlphaBot"
BOT_EMOJI = "A"
BOT_BIO = "test alpha"
BOT_AUTHOR = "test"

def decide(state):
    return ("rest",)
"""

_BOT_B = """\
BOT_NAME = "BetaBot"
BOT_EMOJI = "B"
BOT_BIO = "test beta"
BOT_AUTHOR = "test"

def decide(state):
    return ("rest",)
"""


def _setup_bots(tmp_path: Path) -> Path:
    """Write two minimal bots and return the bots directory."""
    bots_dir = tmp_path / "bots"
    bots_dir.mkdir()
    (bots_dir / "alpha.py").write_text(_BOT_A, encoding="utf-8")
    (bots_dir / "beta.py").write_text(_BOT_B, encoding="utf-8")
    return bots_dir


# -- Cycle 1: Registration and help ------------------------------------------


class TestPlayRegistered:
    """play subcommand is registered in the CLI."""

    def test_play_appears_in_help(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        out, _err, code = _run_main(["--help"], capsys)
        assert code == 0
        assert "play" in out

    def test_play_help_exits_zero(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        out, _err, code = _run_main(["play", "--help"], capsys)
        assert code == 0
        assert "--bots-dir" in out
        assert "--seed" in out
        assert "--speed" in out
        assert "--no-watch" in out


# -- Cycle 2: Error cases ----------------------------------------------------


class TestPlayErrors:
    """Error cases exit non-zero with messages."""

    def test_missing_bots_dir_exits_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        fake_dir = tmp_path / "nonexistent"
        _out, err, code = _run_main(
            ["play", "--bots-dir", str(fake_dir), "--no-watch"], capsys,
        )
        assert code == 1
        assert "not found" in err.lower()

    def test_validation_failure_exits_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        bots_dir = tmp_path / "bots"
        bots_dir.mkdir()
        # Bot missing decide() function
        bad_bot = 'BOT_NAME = "Bad"\nBOT_EMOJI = "X"\n'
        (bots_dir / "bad.py").write_text(bad_bot, encoding="utf-8")
        _out, err, code = _run_main(
            ["play", "--bots-dir", str(bots_dir), "--no-watch"], capsys,
        )
        assert code == 1
        assert "fix" in err.lower() or "validation" in err.lower()

    def test_fewer_than_2_bots_exits_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        bots_dir = tmp_path / "bots"
        bots_dir.mkdir()
        (bots_dir / "alpha.py").write_text(_BOT_A, encoding="utf-8")
        _out, err, code = _run_main(
            ["play", "--bots-dir", str(bots_dir), "--no-watch"], capsys,
        )
        assert code == 1
        assert "2" in err


# -- Cycle 3: Happy path with --no-watch --------------------------------------


class TestPlayNoWatch:
    """--no-watch prints summary without playback."""

    def test_play_no_watch_exits_zero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        monkeypatch.chdir(tmp_path)
        out, _err, code = _run_main(
            ["play", "--bots-dir", str(bots_dir), "--no-watch", "--seed", "42"],
            capsys,
        )
        assert code == 0

    def test_play_no_watch_prints_winner(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        monkeypatch.chdir(tmp_path)
        out, _err, code = _run_main(
            ["play", "--bots-dir", str(bots_dir), "--no-watch", "--seed", "42"],
            capsys,
        )
        assert "Winner:" in out

    def test_play_no_watch_prints_rounds(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        monkeypatch.chdir(tmp_path)
        out, _err, code = _run_main(
            ["play", "--bots-dir", str(bots_dir), "--no-watch", "--seed", "42"],
            capsys,
        )
        assert "Rounds:" in out

    def test_play_no_watch_prints_saved_path(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        monkeypatch.chdir(tmp_path)
        out, _err, code = _run_main(
            ["play", "--bots-dir", str(bots_dir), "--no-watch", "--seed", "42"],
            capsys,
        )
        assert "Saved:" in out

    def test_play_no_watch_saves_replay_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        monkeypatch.chdir(tmp_path)
        _run_main(
            ["play", "--bots-dir", str(bots_dir), "--no-watch", "--seed", "42"],
            capsys,
        )
        results_dir = tmp_path / "results"
        json_files = list(results_dir.glob("*.json"))
        assert len(json_files) >= 1

    def test_play_deterministic_with_seed(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        monkeypatch.chdir(tmp_path)
        out1, _, _ = _run_main(
            ["play", "--bots-dir", str(bots_dir), "--no-watch", "--seed", "99"],
            capsys,
        )
        out2, _, _ = _run_main(
            ["play", "--bots-dir", str(bots_dir), "--no-watch", "--seed", "99"],
            capsys,
        )
        winner1 = [ln for ln in out1.splitlines() if "Winner:" in ln][0]
        winner2 = [ln for ln in out2.splitlines() if "Winner:" in ln][0]
        # Same seed -> same winner emoji
        assert winner1.split("|")[0] == winner2.split("|")[0]
