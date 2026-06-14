"""Tests for the ``killswitch doctor`` diagnostic command (T73.9).

Covers three fixture bots run against the shipped pool:
  * a healthy bot (always rests near no one is NOT healthy; we reuse aggro) -> exit 0
  * a locked-action bot (attempts a locked ``trap``) -> locked attempts, exit != 0
  * a plague-prone bot (always rests, far from enemies) -> plague rounds > 0
"""
from __future__ import annotations

import textwrap
from pathlib import Path

POOL_DIR = str(Path(__file__).resolve().parent.parent / "agentgrounds" / "wars" / "builtin_bots")

HEALTHY_BOT = str(
    Path(__file__).resolve().parent.parent / "agentgrounds" / "wars" / "builtin_bots" / "example_aggro.py"
)

LOCKED_SRC = textwrap.dedent(
    '''
    """Always attempts a locked trap action."""
    BOT_NAME = "Locky"
    BOT_EMOJI = "\U0001F512"

    def decide(state):
        return ("trap", "north")
    '''
)

PLAGUE_SRC = textwrap.dedent(
    '''
    """Always rests far from enemies -> accrues plague."""
    BOT_NAME = "Resty"
    BOT_EMOJI = "\U0001F634"

    def decide(state):
        return ("rest",)
    '''
)


def _write_bot(tmp_path: Path, name: str, src: str) -> str:
    f = tmp_path / name
    f.write_text(src, encoding="utf-8")
    return str(f)


def _invoke(args_list: list[str]) -> tuple[int, str]:
    """Invoke the doctor command's run() with parsed args; return (exit_code, stdout)."""
    import argparse
    import io
    import contextlib

    from agentgrounds.wars.cli import cmd_doctor

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    cmd_doctor.register(sub)
    args = parser.parse_args(["doctor", *args_list])

    buf = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(buf):
        try:
            args.func(args)
        except SystemExit as exc:
            code = int(exc.code or 0)
    return code, buf.getvalue()


# ---------------------------------------------------------------------------
# Cycle 1: healthy bot -> exit 0, report has all sections
# ---------------------------------------------------------------------------


class TestHealthyBot:
    def test_exit_zero_and_all_sections(self) -> None:
        code, out = _invoke(
            [HEALTHY_BOT, "--pool-dir", POOL_DIR, "--matches", "2", "--seed", "1"]
        )
        assert code == 0, out
        for section in (
            "locked-action",
            "plague",
            "forced-rest",
            "storm",
            "placement",
        ):
            assert section.lower() in out.lower(), f"missing section {section!r}\n{out}"


# ---------------------------------------------------------------------------
# Cycle 2: locked-action bot -> reports attempts, non-zero exit
# ---------------------------------------------------------------------------


class TestLockedActionBot:
    def test_reports_locked_attempts_and_nonzero_exit(self, tmp_path: Path) -> None:
        bot = _write_bot(tmp_path, "locky.py", LOCKED_SRC)
        code, out = _invoke(
            [bot, "--pool-dir", POOL_DIR, "--matches", "2", "--seed", "2"]
        )
        assert code != 0, out
        assert "locked-action" in out.lower()
        # locked-action attempt count should be > 0 somewhere in the report
        assert any(ch.isdigit() for ch in out)
        assert "0" != _locked_total(out)


def _locked_total(out: str) -> str:
    """Best-effort: confirm a non-zero locked-action total appears."""
    for line in out.splitlines():
        if "locked" in line.lower():
            digits = "".join(c for c in line if c.isdigit())
            if digits and int(digits) > 0:
                return digits
    return "0"


# ---------------------------------------------------------------------------
# Cycle 3: plague-prone bot -> plague rounds > 0
# ---------------------------------------------------------------------------


class TestPlagueBot:
    def test_reports_plague_rounds(self, tmp_path: Path) -> None:
        bot = _write_bot(tmp_path, "resty.py", PLAGUE_SRC)
        code, out = _invoke(
            [bot, "--pool-dir", POOL_DIR, "--matches", "3", "--seed", "5"]
        )
        # plague-prone bot does not disconnect / lock -> exit 0
        assert code == 0, out
        assert "plague" in out.lower()
        plague_n = _section_total(out, "plague")
        assert plague_n > 0, f"expected plague rounds > 0\n{out}"


def _section_total(out: str, keyword: str) -> int:
    for line in out.splitlines():
        if keyword in line.lower():
            digits = "".join(c for c in line if c.isdigit())
            if digits:
                return int(digits)
    return 0


# ---------------------------------------------------------------------------
# Cycle 4: build_diagnostics returns a structured report (testable core)
# ---------------------------------------------------------------------------


class TestBuildDiagnostics:
    def test_report_structure(self) -> None:
        from agentgrounds.wars.cli.cmd_doctor import build_diagnostics

        report = build_diagnostics(
            target_path=HEALTHY_BOT, pool_dir=POOL_DIR, matches=2, seed=1
        )
        assert report["matches"] == 2
        assert "emoji" in report
        agg = report["aggregate"]
        for key in (
            "locked_action_attempts",
            "plague_rounds",
            "forced_rest_rounds",
            "storm_damage",
            "storm_deaths",
            "disconnects",
        ):
            assert key in agg, f"missing aggregate key {key!r}"
        assert len(report["runs"]) == 2
        for run in report["runs"]:
            assert "placement" in run

    def test_locked_bot_flagged(self, tmp_path: Path) -> None:
        from agentgrounds.wars.cli.cmd_doctor import build_diagnostics

        bot = _write_bot(tmp_path, "locky.py", LOCKED_SRC)
        report = build_diagnostics(
            target_path=bot, pool_dir=POOL_DIR, matches=2, seed=2
        )
        assert report["aggregate"]["locked_action_attempts"] > 0
        assert report["healthy"] is False
