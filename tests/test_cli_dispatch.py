"""Tests for the CLI dispatcher skeleton (T14.3)."""
from __future__ import annotations

import pytest


def _run_main(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[str, int]:
    """Run main() and return (stdout, exit_code).

    For --help/--version argparse raises SystemExit(0).
    For missing/bad subcommands it raises SystemExit(2).
    For stub handlers it raises SystemExit(1).
    """
    from npcwars.cli import main

    try:
        main(argv)
        return capsys.readouterr().out, 0
    except SystemExit as exc:
        return capsys.readouterr().out, exc.code


class TestHelpAndVersion:
    """--help and --version flags."""

    def test_help_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_main(["--help"], capsys)
        assert code == 0

    def test_help_lists_subcommands(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_main(["--help"], capsys)
        for subcmd in ("init", "wizard", "validate", "battle"):
            assert subcmd in out, f"Expected '{subcmd}' in help output"

    def test_version_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_main(["--version"], capsys)
        assert code == 0

    def test_version_contains_version_string(self, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_main(["--version"], capsys)
        # Should contain "npcwars" and some version-like string (digits or "dev")
        assert "npcwars" in out


class TestSubcommandHelp:
    """Each subcommand --help exits 0."""

    @pytest.mark.parametrize("subcmd", ["init", "wizard", "validate", "battle"])
    def test_subcommand_help_exits_zero(self, subcmd: str, capsys: pytest.CaptureFixture[str]) -> None:
        out, code = _run_main([subcmd, "--help"], capsys)
        assert code == 0


class TestNoArgs:
    """No arguments should exit non-zero."""

    def test_no_args_exits_nonzero(self, capsys: pytest.CaptureFixture[str]) -> None:
        _out, code = _run_main([], capsys)
        assert code != 0

    def test_nonexistent_subcommand_exits_nonzero(self, capsys: pytest.CaptureFixture[str]) -> None:
        _out, code = _run_main(["nonexistent"], capsys)
        assert code != 0
