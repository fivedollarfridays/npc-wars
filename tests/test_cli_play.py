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


# -- Cycle 4: --no-fx flag ---------------------------------------------------


class TestPlayNoFxFlag:
    """--no-fx flag is registered and defaults to False."""

    def test_no_fx_appears_in_help(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        out, _err, code = _run_main(["play", "--help"], capsys)
        assert code == 0
        assert "--no-fx" in out

    def test_no_fx_defaults_false(self) -> None:
        """When --no-fx is not passed, args.no_fx is False."""
        import argparse

        from agentgrounds.wars.cli.cmd_play import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["play", "--bots-dir", "bots", "--no-watch"])
        assert args.no_fx is False

    def test_no_fx_true_when_passed(self) -> None:
        """When --no-fx is passed, args.no_fx is True."""
        import argparse

        from agentgrounds.wars.cli.cmd_play import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["play", "--no-fx", "--no-watch"])
        assert args.no_fx is True


# -- Cycle 5: Sub-frame rendering in _play_back ------------------------------

_MATCH_DATA_WITH_COMBAT = {
    "players": [
        {"name": "A", "emoji": "A"},
        {"name": "B", "emoji": "B"},
    ],
    "grid_size": 5,
    "rounds": [
        {
            "round": 1,
            "storm_border": 0,
            "positions": [
                {"emoji": "A", "x": 1, "y": 1, "alive": True, "hp": 100, "energy": 5},
                {"emoji": "B", "x": 2, "y": 1, "alive": True, "hp": 80, "energy": 4},
            ],
            "events": [{"type": "hit", "attacker": "A", "target": "B", "damage": 20}],
        },
    ],
    "winner": "A",
    "duration_rounds": 1,
}

_MATCH_DATA_NO_COMBAT = {
    "players": [
        {"name": "A", "emoji": "A"},
        {"name": "B", "emoji": "B"},
    ],
    "grid_size": 5,
    "rounds": [
        {
            "round": 1,
            "storm_border": 0,
            "positions": [
                {"emoji": "A", "x": 1, "y": 1, "alive": True, "hp": 100, "energy": 5},
                {"emoji": "B", "x": 3, "y": 3, "alive": True, "hp": 100, "energy": 5},
            ],
            "events": [],
        },
    ],
    "winner": "A",
    "duration_rounds": 1,
}


class TestPlayBackSubFrames:
    """_play_back renders action sub-frames for combat rounds."""

    def test_combat_round_calls_render_action_frame(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Combat rounds should trigger render_action_frame."""
        from unittest.mock import patch

        from agentgrounds.wars.cli.renderer import TerminalRenderer

        with patch("time.sleep"), patch.object(
            TerminalRenderer, "render_action_frame", return_value="action"
        ) as mock_af, patch.object(
            TerminalRenderer, "render_frame", return_value="resolve"
        ), patch.object(
            TerminalRenderer, "render_winner", return_value="winner"
        ), patch.object(
            TerminalRenderer, "render_final_frame", return_value="final"
        ), patch.object(
            TerminalRenderer, "render_standings", return_value="standings"
        ), patch.object(
            TerminalRenderer, "exit_alt_screen", return_value=""
        ):
            from agentgrounds.wars.cli.cmd_play import _play_back

            _play_back(_MATCH_DATA_WITH_COMBAT, 1000.0, "f.json")
            mock_af.assert_called_once()

    def test_quiet_round_skips_action_frame(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Rounds without combat should NOT call render_action_frame."""
        from unittest.mock import patch

        from agentgrounds.wars.cli.renderer import TerminalRenderer

        with patch("time.sleep"), patch.object(
            TerminalRenderer, "render_action_frame", return_value="action"
        ) as mock_af, patch.object(
            TerminalRenderer, "render_frame", return_value="resolve"
        ), patch.object(
            TerminalRenderer, "render_winner", return_value="winner"
        ), patch.object(
            TerminalRenderer, "render_final_frame", return_value="final"
        ), patch.object(
            TerminalRenderer, "render_standings", return_value="standings"
        ), patch.object(
            TerminalRenderer, "exit_alt_screen", return_value=""
        ):
            from agentgrounds.wars.cli.cmd_play import _play_back

            _play_back(_MATCH_DATA_NO_COMBAT, 1000.0, "f.json")
            mock_af.assert_not_called()

    def test_no_fx_skips_action_frame_even_with_combat(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """--no-fx should skip action sub-frames even for combat rounds."""
        from unittest.mock import patch

        from agentgrounds.wars.cli.renderer import TerminalRenderer

        with patch("time.sleep"), patch.object(
            TerminalRenderer, "render_action_frame", return_value="action"
        ) as mock_af, patch.object(
            TerminalRenderer, "render_frame", return_value="resolve"
        ), patch.object(
            TerminalRenderer, "render_winner", return_value="winner"
        ), patch.object(
            TerminalRenderer, "render_final_frame", return_value="final"
        ), patch.object(
            TerminalRenderer, "render_standings", return_value="standings"
        ), patch.object(
            TerminalRenderer, "exit_alt_screen", return_value=""
        ):
            from agentgrounds.wars.cli.cmd_play import _play_back

            _play_back(
                _MATCH_DATA_WITH_COMBAT, 1000.0, "f.json", no_fx=True,
            )
            mock_af.assert_not_called()

    def test_combat_round_timing_split(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Combat rounds split delay: 30% action, 70% resolve."""
        from unittest.mock import call, patch

        from agentgrounds.wars.cli.renderer import TerminalRenderer

        with patch("time.sleep") as mock_sleep, patch.object(
            TerminalRenderer, "render_action_frame", return_value="action"
        ), patch.object(
            TerminalRenderer, "render_frame", return_value="resolve"
        ), patch.object(
            TerminalRenderer, "render_winner", return_value="winner"
        ), patch.object(
            TerminalRenderer, "render_final_frame", return_value="final"
        ), patch.object(
            TerminalRenderer, "render_standings", return_value="standings"
        ), patch.object(
            TerminalRenderer, "exit_alt_screen", return_value=""
        ):
            from agentgrounds.wars.cli.cmd_play import _play_back

            # speed=1.0 => delay=1.0 => action=0.3, resolve=0.7
            _play_back(_MATCH_DATA_WITH_COMBAT, 1.0, "f.json")
            sleep_calls = mock_sleep.call_args_list
            assert call(pytest.approx(0.3, abs=0.01)) in sleep_calls
            assert call(pytest.approx(0.7, abs=0.01)) in sleep_calls
