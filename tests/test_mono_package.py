"""Tests for mono-package structure (T66.1).

Verifies that `agentgrounds` dispatches to both Kill Switch and Code Circuit,
and that both games are accessible via their CLI entry points.
"""

from __future__ import annotations

import pytest


def _run_platform(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[str, int]:
    """Run platform main() and return (stdout, exit_code)."""
    from agentgrounds.__main__ import main

    try:
        main(argv)
        return capsys.readouterr().out, 0
    except SystemExit as exc:
        return capsys.readouterr().out, exc.code


class TestPlatformHelp:
    """agentgrounds --help lists both games."""

    def test_help_lists_killswitch(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_platform(["--help"], capsys)
        assert "killswitch" in out

    def test_help_lists_circuit(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_platform(["--help"], capsys)
        assert "circuit" in out

    def test_help_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        _out, code = _run_platform(["--help"], capsys)
        assert code == 0


class TestPlatformDispatch:
    """agentgrounds routes killswitch and circuit to correct modules."""

    def test_killswitch_is_valid_game(self) -> None:
        from agentgrounds.__main__ import GAMES

        assert "killswitch" in GAMES

    def test_circuit_is_valid_game(self) -> None:
        from agentgrounds.__main__ import GAMES

        assert "circuit" in GAMES

    def test_unknown_game_exits_nonzero(self, capsys: pytest.CaptureFixture[str]) -> None:
        _out, code = _run_platform(["nonexistent"], capsys)
        assert code == 2

    def test_wars_still_works_as_alias(self) -> None:
        """Backward compat: 'wars' should still be a valid game."""
        from agentgrounds.__main__ import GAMES

        assert "wars" in GAMES


class TestKillSwitchCLI:
    """agentgrounds killswitch subcommands."""

    def test_killswitch_help_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_platform(["killswitch", "--help"], capsys)
        assert code == 0
        assert "play" in out

    def test_killswitch_no_args_exits_nonzero(self, capsys: pytest.CaptureFixture[str]) -> None:
        _out, code = _run_platform(["killswitch"], capsys)
        assert code == 2


class TestCircuitCLI:
    """agentgrounds circuit subcommands."""

    def test_circuit_help_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_platform(["circuit", "--help"], capsys)
        assert code == 0
        assert "race" in out

    def test_circuit_no_args_exits_nonzero(self, capsys: pytest.CaptureFixture[str]) -> None:
        _out, code = _run_platform(["circuit"], capsys)
        assert code == 2
