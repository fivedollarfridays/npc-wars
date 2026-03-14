"""Tests for the npcwars battle CLI command (T14.7)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

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


def _run_battle(
    argv: list[str], capsys: pytest.CaptureFixture[str],
) -> tuple[str, str, int]:
    """Run battle via main() and return (stdout, stderr, exit_code)."""
    from npcwars.cli import main

    try:
        main(argv)
        captured = capsys.readouterr()
        return captured.out, captured.err, 0
    except SystemExit as exc:
        captured = capsys.readouterr()
        return captured.out, captured.err, exc.code


class TestBattleHelp:
    """battle --help works."""

    def test_help_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, _err, code = _run_battle(["battle", "--help"], capsys)
        assert code == 0
        assert "battle" in out.lower()

    def test_help_shows_options(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, _err, code = _run_battle(["battle", "--help"], capsys)
        assert "--bots-dir" in out
        assert "--seed" in out
        assert "--replay" in out


class TestBattleRuns:
    """Battle with valid bots exits 0 and prints a winner."""

    def test_battle_exits_zero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        out, _err, code = _run_battle(
            ["battle", "--bots-dir", str(bots_dir), "--seed", "42"], capsys,
        )
        assert code == 0

    def test_battle_prints_winner(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        out, _err, code = _run_battle(
            ["battle", "--bots-dir", str(bots_dir), "--seed", "42"], capsys,
        )
        assert "Winner:" in out

    def test_battle_prints_rounds(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        out, _err, code = _run_battle(
            ["battle", "--bots-dir", str(bots_dir), "--seed", "42"], capsys,
        )
        assert "Rounds:" in out


class TestBattleSeed:
    """--seed produces deterministic output."""

    def test_same_seed_same_winner(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        out1, _err1, _code1 = _run_battle(
            ["battle", "--bots-dir", str(bots_dir), "--seed", "99"], capsys,
        )
        out2, _err2, _code2 = _run_battle(
            ["battle", "--bots-dir", str(bots_dir), "--seed", "99"], capsys,
        )
        # Extract winner lines
        winner1 = [ln for ln in out1.splitlines() if "Winner:" in ln][0]
        winner2 = [ln for ln in out2.splitlines() if "Winner:" in ln][0]
        assert winner1 == winner2


class TestBattleReplay:
    """--replay writes JSON file."""

    def test_replay_creates_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        replay_dir = tmp_path / "replays"
        out, _err, code = _run_battle(
            ["battle", "--bots-dir", str(bots_dir), "--seed", "42",
             "--replay", str(replay_dir)],
            capsys,
        )
        assert code == 0
        json_files = list(replay_dir.glob("*.json"))
        assert len(json_files) >= 1

    def test_replay_json_parseable(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        replay_dir = tmp_path / "replays"
        _run_battle(
            ["battle", "--bots-dir", str(bots_dir), "--seed", "42",
             "--replay", str(replay_dir)],
            capsys,
        )
        json_file = next(replay_dir.glob("*.json"))
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert "winner" in data
        assert "duration_rounds" in data

    def test_replay_prints_filepath(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        bots_dir = _setup_bots(tmp_path)
        replay_dir = tmp_path / "replays"
        out, _err, code = _run_battle(
            ["battle", "--bots-dir", str(bots_dir), "--seed", "42",
             "--replay", str(replay_dir)],
            capsys,
        )
        assert "Replay saved:" in out


class TestBattleBotsDir:
    """--bots-dir overrides default."""

    def test_custom_bots_dir(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        custom_dir = tmp_path / "my_bots"
        custom_dir.mkdir()
        (custom_dir / "alpha.py").write_text(_BOT_A, encoding="utf-8")
        (custom_dir / "beta.py").write_text(_BOT_B, encoding="utf-8")
        out, _err, code = _run_battle(
            ["battle", "--bots-dir", str(custom_dir), "--seed", "42"], capsys,
        )
        assert code == 0
        assert "AlphaBot" in out
        assert "BetaBot" in out


class TestBattleErrors:
    """Error cases exit non-zero."""

    def test_missing_bots_dir_exits_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        fake_dir = tmp_path / "nonexistent"
        _out, err, code = _run_battle(
            ["battle", "--bots-dir", str(fake_dir)], capsys,
        )
        assert code != 0

    def test_fewer_than_2_bots_exits_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        bots_dir = tmp_path / "bots"
        bots_dir.mkdir()
        (bots_dir / "alpha.py").write_text(_BOT_A, encoding="utf-8")
        _out, err, code = _run_battle(
            ["battle", "--bots-dir", str(bots_dir)], capsys,
        )
        assert code != 0

    def test_empty_bots_dir_exits_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        bots_dir = tmp_path / "bots"
        bots_dir.mkdir()
        _out, err, code = _run_battle(
            ["battle", "--bots-dir", str(bots_dir)], capsys,
        )
        assert code != 0
