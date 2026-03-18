"""Tests for agentgrounds wars sim — batch match runner."""
from __future__ import annotations

import json
import os
from pathlib import Path


def _builtin_bots_dir() -> str:
    """Return the path to builtin bots."""
    return str(Path(__file__).resolve().parent.parent / "agentgrounds" / "wars" / "builtin_bots")


# ---------------------------------------------------------------------------
# Cycle 1: basic run creates output files with valid JSON
# ---------------------------------------------------------------------------


class TestSimBasicRun:
    """A small sim run creates match files and summary."""

    def test_creates_match_files(self, tmp_path: Path) -> None:
        from agentgrounds.wars.cli.cmd_sim import run_sim

        output = str(tmp_path / "out")
        run_sim(
            bots_dir=_builtin_bots_dir(),
            matches=3,
            output_dir=output,
            seed=42,
            parallel=False,
            quiet=True,
        )
        for i in range(1, 4):
            f = os.path.join(output, f"match_{i:04d}.json")
            assert os.path.isfile(f), f"Missing {f}"

    def test_match_files_are_valid_json(self, tmp_path: Path) -> None:
        from agentgrounds.wars.cli.cmd_sim import run_sim

        output = str(tmp_path / "out")
        run_sim(
            bots_dir=_builtin_bots_dir(),
            matches=2,
            output_dir=output,
            seed=42,
            parallel=False,
            quiet=True,
        )
        for i in range(1, 3):
            f = os.path.join(output, f"match_{i:04d}.json")
            with open(f) as fh:
                data = json.load(fh)
            assert "winner" in data
            assert "duration_rounds" in data
            assert "players" in data

    def test_creates_summary_file(self, tmp_path: Path) -> None:
        from agentgrounds.wars.cli.cmd_sim import run_sim

        output = str(tmp_path / "out")
        run_sim(
            bots_dir=_builtin_bots_dir(),
            matches=3,
            output_dir=output,
            seed=42,
            parallel=False,
            quiet=True,
        )
        summary_path = os.path.join(output, "sim_summary.json")
        assert os.path.isfile(summary_path)
        with open(summary_path) as fh:
            data = json.load(fh)
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# Cycle 2: summary JSON has required keys and correct values
# ---------------------------------------------------------------------------


class TestSimSummary:
    """Summary JSON contains all required aggregate fields."""

    def _run_and_load_summary(self, tmp_path: Path, matches: int = 5) -> dict:
        from agentgrounds.wars.cli.cmd_sim import run_sim

        output = str(tmp_path / "out")
        run_sim(
            bots_dir=_builtin_bots_dir(),
            matches=matches,
            output_dir=output,
            seed=100,
            parallel=False,
            quiet=True,
        )
        with open(os.path.join(output, "sim_summary.json")) as fh:
            return json.load(fh)

    def test_total_matches(self, tmp_path: Path) -> None:
        summary = self._run_and_load_summary(tmp_path, matches=5)
        assert summary["total_matches"] == 5

    def test_match_length_stats(self, tmp_path: Path) -> None:
        summary = self._run_and_load_summary(tmp_path, matches=5)
        for key in ("avg_match_length", "median_match_length", "min_match_length", "max_match_length"):
            assert key in summary, f"Missing key: {key}"
            assert isinstance(summary[key], (int, float))
        assert summary["min_match_length"] <= summary["avg_match_length"] <= summary["max_match_length"]

    def test_winner_distribution(self, tmp_path: Path) -> None:
        summary = self._run_and_load_summary(tmp_path, matches=5)
        assert "winner_distribution" in summary
        dist = summary["winner_distribution"]
        assert isinstance(dist, dict)
        assert sum(dist.values()) == 5

    def test_placement_distribution(self, tmp_path: Path) -> None:
        summary = self._run_and_load_summary(tmp_path, matches=5)
        assert "placement_distribution" in summary
        placements = summary["placement_distribution"]
        assert isinstance(placements, dict)

    def test_avg_agents_alive_by_round(self, tmp_path: Path) -> None:
        summary = self._run_and_load_summary(tmp_path, matches=5)
        assert "avg_agents_alive_by_round" in summary
        alive_list = summary["avg_agents_alive_by_round"]
        assert isinstance(alive_list, list)
        assert len(alive_list) > 0
        # First round should have all bots alive
        assert alive_list[0] >= 2.0

    def test_timing_total_duration(self, tmp_path: Path) -> None:
        summary = self._run_and_load_summary(tmp_path, matches=3)
        timing = summary["timing"]
        assert timing["total_duration_s"] > 0
        assert isinstance(timing["total_duration_s"], float)

    def test_timing_per_match_splits(self, tmp_path: Path) -> None:
        summary = self._run_and_load_summary(tmp_path, matches=3)
        timing = summary["timing"]
        assert len(timing["match_durations_s"]) == 3
        assert all(d > 0 for d in timing["match_durations_s"])

    def test_timing_stats(self, tmp_path: Path) -> None:
        summary = self._run_and_load_summary(tmp_path, matches=3)
        timing = summary["timing"]
        assert timing["avg_match_duration_s"] > 0
        assert timing["min_match_duration_s"] <= timing["avg_match_duration_s"]
        assert timing["avg_match_duration_s"] <= timing["max_match_duration_s"]
        assert timing["matches_per_second"] > 0


# ---------------------------------------------------------------------------
# Cycle 3: seed reproducibility
# ---------------------------------------------------------------------------


class TestSimSeedReproducibility:
    """Same seed + bots produces identical summary."""

    def test_deterministic_with_same_seed(self, tmp_path: Path) -> None:
        from agentgrounds.wars.cli.cmd_sim import run_sim

        out1 = str(tmp_path / "run1")
        out2 = str(tmp_path / "run2")
        for out in (out1, out2):
            run_sim(
                bots_dir=_builtin_bots_dir(),
                matches=5,
                output_dir=out,
                seed=42,
                parallel=False,
                quiet=True,
            )
        with open(os.path.join(out1, "sim_summary.json")) as f1, \
             open(os.path.join(out2, "sim_summary.json")) as f2:
            s1 = json.load(f1)
            s2 = json.load(f2)
        assert s1["winner_distribution"] == s2["winner_distribution"]
        assert s1["total_matches"] == s2["total_matches"]
        assert s1["avg_match_length"] == s2["avg_match_length"]

    def test_different_seeds_may_differ(self, tmp_path: Path) -> None:
        """Different seeds should (with high probability) produce different results."""
        from agentgrounds.wars.cli.cmd_sim import run_sim

        out1 = str(tmp_path / "run1")
        out2 = str(tmp_path / "run2")
        run_sim(bots_dir=_builtin_bots_dir(), matches=10, output_dir=out1, seed=1, parallel=False, quiet=True)
        run_sim(bots_dir=_builtin_bots_dir(), matches=10, output_dir=out2, seed=9999, parallel=False, quiet=True)
        with open(os.path.join(out1, "sim_summary.json")) as f1, \
             open(os.path.join(out2, "sim_summary.json")) as f2:
            s1 = json.load(f1)
            s2 = json.load(f2)
        # With 10 matches and very different seeds, at least one stat should differ
        differs = (
            s1["winner_distribution"] != s2["winner_distribution"]
            or s1["avg_match_length"] != s2["avg_match_length"]
        )
        assert differs, "Different seeds produced identical results — likely not seeded properly"


# ---------------------------------------------------------------------------
# Cycle 4: parallel mode
# ---------------------------------------------------------------------------


class TestSimParallel:
    """Parallel mode produces same structure as sequential."""

    def test_parallel_creates_files(self, tmp_path: Path) -> None:
        from agentgrounds.wars.cli.cmd_sim import run_sim

        output = str(tmp_path / "out")
        run_sim(
            bots_dir=_builtin_bots_dir(),
            matches=4,
            output_dir=output,
            seed=42,
            parallel=True,
            quiet=True,
        )
        for i in range(1, 5):
            assert os.path.isfile(os.path.join(output, f"match_{i:04d}.json"))
        assert os.path.isfile(os.path.join(output, "sim_summary.json"))

    def test_parallel_summary_has_required_keys(self, tmp_path: Path) -> None:
        from agentgrounds.wars.cli.cmd_sim import run_sim

        output = str(tmp_path / "out")
        run_sim(
            bots_dir=_builtin_bots_dir(),
            matches=4,
            output_dir=output,
            seed=42,
            parallel=True,
            quiet=True,
        )
        with open(os.path.join(output, "sim_summary.json")) as fh:
            summary = json.load(fh)
        assert summary["total_matches"] == 4
        assert "winner_distribution" in summary


# ---------------------------------------------------------------------------
# Cycle 5: CLI integration
# ---------------------------------------------------------------------------


class TestSimCLIRegistration:
    """sim subcommand is registered in the wars CLI."""

    def test_sim_appears_in_subcommands(self) -> None:
        from agentgrounds.wars.cli import _build_parser

        parser = _build_parser()
        # Check that 'sim' is a valid subcommand
        # Parse with sim and verify it doesn't error
        args = parser.parse_args(["sim", "--matches", "1", "--quiet"])
        assert args.subcommand == "sim"

    def test_sim_default_matches(self) -> None:
        from agentgrounds.wars.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["sim", "--quiet"])
        assert args.matches == 10
