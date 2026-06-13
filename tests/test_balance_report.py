"""Tests for the balance regression harness (T73.3).

Covers report shape, determinism, kill-cause classification, and the
threshold check in scripts/check_balance.py (both pass and fail paths).
"""
from __future__ import annotations

import json
from pathlib import Path


def _builtin_bots_dir() -> str:
    """Return the path to the shipped builtin bot pool."""
    return str(
        Path(__file__).resolve().parent.parent
        / "agentgrounds" / "wars" / "builtin_bots"
    )


# ---------------------------------------------------------------------------
# Kill-cause classification
# ---------------------------------------------------------------------------


class TestKillCauseClassification:
    """classify_kill_cause distinguishes combat/storm/disconnect/tiebreaker."""

    def _match(self) -> dict:
        return {
            "rounds": [
                {"round": 3, "positions": [{"emoji": "💀", "action": "disconnected"}]},
                {"round": 4, "positions": [{"emoji": "🗡", "action": "attack up"}]},
            ],
            "eliminations": [
                {"emoji": "💀", "round": 3, "cause": "combat", "killed_by": "unknown"},
                {"emoji": "🔥", "round": 2, "cause": "storm", "killed_by": "storm"},
                {"emoji": "⚡", "round": 5, "cause": "tiebreaker", "killed_by": "tiebreaker"},
                {"emoji": "🗡", "round": 4, "cause": "combat", "killed_by": "🤖"},
            ],
        }

    def test_disconnect_detected(self) -> None:
        from agentgrounds.wars.cli.sim_balance import classify_kill_cause

        m = self._match()
        assert classify_kill_cause(m, m["eliminations"][0]) == "disconnect"

    def test_storm(self) -> None:
        from agentgrounds.wars.cli.sim_balance import classify_kill_cause

        m = self._match()
        assert classify_kill_cause(m, m["eliminations"][1]) == "storm"

    def test_tiebreaker(self) -> None:
        from agentgrounds.wars.cli.sim_balance import classify_kill_cause

        m = self._match()
        assert classify_kill_cause(m, m["eliminations"][2]) == "tiebreaker"

    def test_combat(self) -> None:
        from agentgrounds.wars.cli.sim_balance import classify_kill_cause

        m = self._match()
        assert classify_kill_cause(m, m["eliminations"][3]) == "combat"


# ---------------------------------------------------------------------------
# Report shape
# ---------------------------------------------------------------------------


class TestReportShape:
    """The balance report has all required sections."""

    def _run(self, tmp_path: Path, matches: int = 4, seed: int = 7) -> dict:
        from agentgrounds.wars.cli.cmd_sim import run_balance_report

        out = str(tmp_path / "balance.json")
        return run_balance_report(
            bots_dir=_builtin_bots_dir(),
            matches=matches,
            output=out,
            seed=seed,
            parallel=False,
            quiet=True,
        )

    def test_writes_file(self, tmp_path: Path) -> None:
        out = str(tmp_path / "balance.json")
        from agentgrounds.wars.cli.cmd_sim import run_balance_report

        run_balance_report(
            bots_dir=_builtin_bots_dir(), matches=3, output=out,
            seed=7, parallel=False, quiet=True,
        )
        assert Path(out).is_file()
        with open(out) as fh:
            assert isinstance(json.load(fh), dict)

    def test_required_keys(self, tmp_path: Path) -> None:
        report = self._run(tmp_path)
        for key in (
            "matches", "seed", "bots", "per_bot_win_rate",
            "per_archetype_win_rate", "kill_cause_distribution",
        ):
            assert key in report, f"Missing key: {key}"

    def test_per_bot_win_rate_sums_to_one(self, tmp_path: Path) -> None:
        report = self._run(tmp_path, matches=5)
        total = sum(report["per_bot_win_rate"].values())
        # Every match has exactly one winner in the pool.
        assert abs(total - 1.0) < 1e-6

    def test_archetypes_present(self, tmp_path: Path) -> None:
        report = self._run(tmp_path)
        archs = report["per_archetype_win_rate"]
        # builtin pool spans Bruiser/Assassin/Tank/Controller/Balanced
        assert "Balanced" in archs
        assert all(0.0 <= v <= 1.0 for v in archs.values())

    def test_kill_cause_keys(self, tmp_path: Path) -> None:
        report = self._run(tmp_path)
        dist = report["kill_cause_distribution"]
        for cause in ("combat", "storm", "disconnect", "tiebreaker"):
            assert cause in dist
            assert isinstance(dist[cause], int)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    """Same seed + match count produces an identical report."""

    def test_deterministic(self, tmp_path: Path) -> None:
        from agentgrounds.wars.cli.cmd_sim import run_balance_report

        r1 = run_balance_report(
            bots_dir=_builtin_bots_dir(), matches=4,
            output=str(tmp_path / "a.json"), seed=11, parallel=False, quiet=True,
        )
        r2 = run_balance_report(
            bots_dir=_builtin_bots_dir(), matches=4,
            output=str(tmp_path / "b.json"), seed=11, parallel=False, quiet=True,
        )
        assert r1["per_bot_win_rate"] == r2["per_bot_win_rate"]
        assert r1["per_archetype_win_rate"] == r2["per_archetype_win_rate"]
        assert r1["kill_cause_distribution"] == r2["kill_cause_distribution"]


# ---------------------------------------------------------------------------
# Threshold check (scripts/check_balance.py)
# ---------------------------------------------------------------------------


class TestThresholdCheck:
    """check_balance fails only when a bot deviates beyond the threshold."""

    def _baseline(self) -> dict:
        return {
            "matches": 30, "seed": 1, "bots": ["🤖", "🐢", "🎯"],
            "per_bot_win_rate": {"🤖": 0.40, "🐢": 0.35, "🎯": 0.25},
            "per_archetype_win_rate": {"Bruiser": 0.40, "Tank": 0.35, "Assassin": 0.25},
            "kill_cause_distribution": {"combat": 100, "storm": 20, "disconnect": 0, "tiebreaker": 2},
        }

    def _write(self, path: Path, data: dict) -> str:
        path.write_text(json.dumps(data))
        return str(path)

    def test_pass_when_within_threshold(self, tmp_path: Path) -> None:
        from scripts.check_balance import main

        base = self._baseline()
        report = json.loads(json.dumps(base))
        report["per_bot_win_rate"]["🤖"] = 0.50  # +10pp, under 15pp
        bp = self._write(tmp_path / "base.json", base)
        rp = self._write(tmp_path / "rep.json", report)
        assert main(["--baseline", bp, "--report", rp]) == 0

    def test_fail_when_beyond_threshold(self, tmp_path: Path) -> None:
        from scripts.check_balance import main

        base = self._baseline()
        report = json.loads(json.dumps(base))
        report["per_bot_win_rate"]["🤖"] = 0.77  # +37pp, the "won 77%" regression
        bp = self._write(tmp_path / "base.json", base)
        rp = self._write(tmp_path / "rep.json", report)
        assert main(["--baseline", bp, "--report", rp]) == 1

    def test_threshold_is_configurable(self, tmp_path: Path) -> None:
        from scripts.check_balance import main

        base = self._baseline()
        report = json.loads(json.dumps(base))
        report["per_bot_win_rate"]["🤖"] = 0.50  # +10pp
        bp = self._write(tmp_path / "base.json", base)
        rp = self._write(tmp_path / "rep.json", report)
        # Tighten threshold to 5pp -> the 10pp move now fails.
        assert main(["--baseline", bp, "--report", rp, "--threshold", "0.05"]) == 1

    def test_compare_returns_failures(self, tmp_path: Path) -> None:
        from scripts.check_balance import compare

        base = self._baseline()
        report = json.loads(json.dumps(base))
        report["per_bot_win_rate"]["🤖"] = 0.77
        failures = compare(base, report, 0.15)
        assert len(failures) == 1
        assert failures[0][0] == "🤖"
