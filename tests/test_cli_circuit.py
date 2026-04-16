"""Tests for Code Circuit CLI (T66.1).

Verifies the `agentgrounds circuit` CLI subcommands.
"""

from __future__ import annotations

import pytest


def _run_circuit(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[str, int]:
    """Run circuit CLI main() and return (stdout, exit_code)."""
    from agentgrounds.circuit.cli import main

    try:
        main(argv)
        return capsys.readouterr().out, 0
    except SystemExit as exc:
        return capsys.readouterr().out, exc.code


class TestCircuitHelp:
    """circuit --help."""

    def test_help_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_circuit(["--help"], capsys)
        assert code == 0

    def test_help_lists_race(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_circuit(["--help"], capsys)
        assert "race" in out


class TestRaceSubcommand:
    """circuit race subcommand."""

    def test_race_help_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_circuit(["race", "--help"], capsys)
        assert code == 0

    def test_race_help_mentions_seed(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_circuit(["race", "--help"], capsys)
        assert "seed" in out.lower()

    def test_race_help_mentions_laps(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_circuit(["race", "--help"], capsys)
        assert "laps" in out.lower()

    def test_no_args_exits_nonzero(self, capsys: pytest.CaptureFixture[str]) -> None:
        _out, code = _run_circuit([], capsys)
        assert code != 0
