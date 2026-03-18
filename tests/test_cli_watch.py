"""Tests for the npcwars watch CLI command (T20.2)."""
from __future__ import annotations

import json
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


# -- Cycle 4: --no-fx flag ---------------------------------------------------


class TestWatchNoFxFlag:
    """--no-fx flag is registered and defaults to False."""

    def test_no_fx_appears_in_help(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        out, _err, code = _run_main(["watch", "--help"], capsys)
        assert code == 0
        assert "--no-fx" in out

    def test_no_fx_defaults_false(self) -> None:
        """When --no-fx is not passed, args.no_fx is False."""
        import argparse

        from agentgrounds.wars.cli.cmd_watch import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["watch", "file.json"])
        assert args.no_fx is False

    def test_no_fx_true_when_passed(self) -> None:
        """When --no-fx is passed, args.no_fx is True."""
        import argparse

        from agentgrounds.wars.cli.cmd_watch import register

        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers()
        register(subs)
        args = parser.parse_args(["watch", "--no-fx", "file.json"])
        assert args.no_fx is True


# -- Cycle 5: Sub-frame rendering in watch ------------------------------------


def _make_combat_match(tmp_path: Path) -> Path:
    """Write a match with combat events and return its path."""
    match_data = {
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
    filepath = tmp_path / "combat_match.json"
    filepath.write_text(json.dumps(match_data), encoding="utf-8")
    return filepath


def _make_quiet_match(tmp_path: Path) -> Path:
    """Write a match with no combat events and return its path."""
    match_data = {
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
    filepath = tmp_path / "quiet_match.json"
    filepath.write_text(json.dumps(match_data), encoding="utf-8")
    return filepath


class TestWatchSubFrames:
    """watch renders action sub-frames for combat rounds."""

    def test_combat_round_calls_render_action_frame(
        self, tmp_path: Path,
    ) -> None:
        filepath = _make_combat_match(tmp_path)
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
            import argparse

            args = argparse.Namespace(
                file=str(filepath), speed=1000.0, no_clear=True, no_fx=False,
            )
            from agentgrounds.wars.cli.cmd_watch import run

            run(args)
            mock_af.assert_called_once()

    def test_quiet_round_skips_action_frame(
        self, tmp_path: Path,
    ) -> None:
        filepath = _make_quiet_match(tmp_path)
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
            import argparse

            args = argparse.Namespace(
                file=str(filepath), speed=1000.0, no_clear=True, no_fx=False,
            )
            from agentgrounds.wars.cli.cmd_watch import run

            run(args)
            mock_af.assert_not_called()

    def test_no_fx_skips_action_frame(
        self, tmp_path: Path,
    ) -> None:
        filepath = _make_combat_match(tmp_path)
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
            import argparse

            args = argparse.Namespace(
                file=str(filepath), speed=1000.0, no_clear=True, no_fx=True,
            )
            from agentgrounds.wars.cli.cmd_watch import run

            run(args)
            mock_af.assert_not_called()

    def test_combat_timing_split(
        self, tmp_path: Path,
    ) -> None:
        filepath = _make_combat_match(tmp_path)
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
            import argparse

            # speed=1.0 => delay=1.0 => action=0.3, resolve=0.7
            args = argparse.Namespace(
                file=str(filepath), speed=1.0, no_clear=True, no_fx=False,
            )
            from agentgrounds.wars.cli.cmd_watch import run

            run(args)
            sleep_calls = mock_sleep.call_args_list
            assert call(pytest.approx(0.3, abs=0.01)) in sleep_calls
            assert call(pytest.approx(0.7, abs=0.01)) in sleep_calls
