"""Integration tests: sim -> analyze end-to-end pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentgrounds.wars.analyzer import run_analysis
from agentgrounds.wars.cli.cmd_sim import run_sim


@pytest.fixture()
def sim_output(tmp_path: Path) -> Path:
    """Run a 5-match sim and return the output directory."""
    bots_dir = str(Path(__file__).resolve().parent.parent / "bots")
    output_dir = str(tmp_path / "sim_out")
    run_sim(
        bots_dir=bots_dir,
        matches=5,
        output_dir=output_dir,
        seed=1,
        parallel=False,
        quiet=True,
    )
    return tmp_path / "sim_out"


class TestSimRunner:
    """Test 1: sim produces expected output files."""

    def test_match_files_created(self, sim_output: Path) -> None:
        match_files = sorted(sim_output.glob("match_*.json"))
        assert len(match_files) == 5

    def test_summary_exists(self, sim_output: Path) -> None:
        assert (sim_output / "sim_summary.json").exists()

    def test_avg_match_length_positive(self, sim_output: Path) -> None:
        summary = json.loads((sim_output / "sim_summary.json").read_text())
        assert summary["avg_match_length"] > 0

    def test_summary_has_required_keys(self, sim_output: Path) -> None:
        summary = json.loads((sim_output / "sim_summary.json").read_text())
        for key in (
            "total_matches",
            "avg_match_length",
            "median_match_length",
            "min_match_length",
            "max_match_length",
            "winner_distribution",
        ):
            assert key in summary, f"Missing key: {key}"

    def test_total_matches_equals_five(self, sim_output: Path) -> None:
        summary = json.loads((sim_output / "sim_summary.json").read_text())
        assert summary["total_matches"] == 5


class TestAnalyzer:
    """Test 2: analyze produces expected output files."""

    def test_heatmaps_json_exists(self, sim_output: Path) -> None:
        analysis_dir = sim_output / "analysis"
        run_analysis(input_dir=sim_output, output_dir=analysis_dir, fmt="json")
        assert (analysis_dir / "heatmaps.json").exists()

    def test_heatmaps_has_required_keys(self, sim_output: Path) -> None:
        analysis_dir = sim_output / "analysis"
        run_analysis(input_dir=sim_output, output_dir=analysis_dir, fmt="json")
        heatmaps = json.loads((analysis_dir / "heatmaps.json").read_text())
        for key in ("kill", "death", "balance"):
            assert key in heatmaps, f"Missing heatmap key: {key}"

    def test_analysis_report_exists(self, sim_output: Path) -> None:
        analysis_dir = sim_output / "analysis"
        run_analysis(input_dir=sim_output, output_dir=analysis_dir, fmt="json")
        assert (analysis_dir / "analysis_report.json").exists()

    def test_analysis_report_has_verdict(self, sim_output: Path) -> None:
        analysis_dir = sim_output / "analysis"
        run_analysis(input_dir=sim_output, output_dir=analysis_dir, fmt="json")
        report = json.loads((analysis_dir / "analysis_report.json").read_text())
        assert "verdict" in report


class TestTimingData:
    """Test: sim_summary.json has timing data."""

    def test_timing_has_total_duration(self, sim_output: Path) -> None:
        summary = json.loads((sim_output / "sim_summary.json").read_text())
        timing = summary["timing"]
        assert "total_duration_s" in timing
        assert isinstance(timing["total_duration_s"], (int, float))
        assert timing["total_duration_s"] > 0

    def test_timing_has_match_durations(self, sim_output: Path) -> None:
        summary = json.loads((sim_output / "sim_summary.json").read_text())
        timing = summary["timing"]
        assert "match_durations_s" in timing
        assert isinstance(timing["match_durations_s"], list)
        assert len(timing["match_durations_s"]) == 5

    def test_timing_has_matches_per_second(self, sim_output: Path) -> None:
        summary = json.loads((sim_output / "sim_summary.json").read_text())
        timing = summary["timing"]
        assert "matches_per_second" in timing
        assert timing["matches_per_second"] > 0


class TestHeatmapGrids:
    """Test: heatmaps.json has kill/death/balance keys with NxN grids."""

    def test_heatmap_grids_are_square(self, sim_output: Path) -> None:
        analysis_dir = sim_output / "analysis"
        run_analysis(input_dir=sim_output, output_dir=analysis_dir, fmt="json")
        heatmaps = json.loads((analysis_dir / "heatmaps.json").read_text())
        # Read grid_size from analysis_report to know expected size
        report = json.loads((analysis_dir / "analysis_report.json").read_text())
        expected = report["grid_size"]
        for key in ("kill", "death", "balance"):
            grid = heatmaps[key]
            assert len(grid) == expected, f"{key} grid has {len(grid)} rows, expected {expected}"
            for row in grid:
                assert len(row) == expected, f"{key} row has {len(row)} cols, expected {expected}"
            assert expected >= 10, f"Grid size {expected} is unexpectedly small"


class TestAnalysisVerdict:
    """Test: analysis_report.json has verdict with match_length and win_rate_spread."""

    def test_verdict_has_match_length(self, sim_output: Path) -> None:
        analysis_dir = sim_output / "analysis"
        run_analysis(input_dir=sim_output, output_dir=analysis_dir, fmt="json")
        report = json.loads((analysis_dir / "analysis_report.json").read_text())
        verdict = report["verdict"]
        assert "match_length" in verdict
        ml = verdict["match_length"]
        assert "avg" in ml
        assert "verdict" in ml
        assert ml["verdict"] in ("PASS", "WARN", "FAIL")

    def test_verdict_has_win_rate_spread(self, sim_output: Path) -> None:
        analysis_dir = sim_output / "analysis"
        run_analysis(input_dir=sim_output, output_dir=analysis_dir, fmt="json")
        report = json.loads((analysis_dir / "analysis_report.json").read_text())
        verdict = report["verdict"]
        assert "win_rate_spread" in verdict
        wrs = verdict["win_rate_spread"]
        assert "max_win_rate" in wrs
        assert "verdict" in wrs
        assert wrs["verdict"] in ("PASS", "WARN", "FAIL")


class TestEnergyCurves:
    """Test: energy_curves.json exists and has at least one placement tier key."""

    def test_energy_curves_has_tier_keys(self, sim_output: Path) -> None:
        analysis_dir = sim_output / "analysis"
        run_analysis(input_dir=sim_output, output_dir=analysis_dir, fmt="json")
        curves = json.loads((analysis_dir / "energy_curves.json").read_text())
        valid_tiers = {"placement_1", "placement_2_3", "placement_4_6", "placement_7_plus"}
        assert len(curves) >= 1, "Expected at least one placement tier"
        for key in curves:
            assert key in valid_tiers, f"Unexpected tier key: {key}"


class TestEndToEnd:
    """Test 3: sim -> analyze pipeline produces valid output."""

    def test_pipeline_produces_all_artifacts(self, tmp_path: Path) -> None:
        bots_dir = str(Path(__file__).resolve().parent.parent / "bots")
        sim_dir = str(tmp_path / "pipeline_sim")

        # Step 1: sim
        summary = run_sim(
            bots_dir=bots_dir,
            matches=5,
            output_dir=sim_dir,
            seed=42,
            parallel=False,
            quiet=True,
        )
        assert summary["total_matches"] == 5

        # Step 2: analyze
        analysis_dir = tmp_path / "pipeline_sim" / "analysis"
        result = run_analysis(
            input_dir=Path(sim_dir),
            output_dir=analysis_dir,
            fmt="json",
        )

        # Verify all artifacts
        assert (analysis_dir / "heatmaps.json").exists()
        assert (analysis_dir / "analysis_report.json").exists()
        assert (analysis_dir / "energy_curves.json").exists()

        # Verify report content
        report = result["report"]
        assert report["match_count"] == 5
        assert "verdict" in report

    def test_energy_curves_produced(self, tmp_path: Path) -> None:
        bots_dir = str(Path(__file__).resolve().parent.parent / "bots")
        sim_dir = str(tmp_path / "energy_sim")

        run_sim(bots_dir=bots_dir, matches=5, output_dir=sim_dir, seed=42, quiet=True)
        analysis_dir = tmp_path / "energy_sim" / "analysis"
        run_analysis(input_dir=Path(sim_dir), output_dir=analysis_dir, fmt="json")

        curves = json.loads((analysis_dir / "energy_curves.json").read_text())
        assert isinstance(curves, dict)
        assert len(curves) > 0, "Expected at least one placement tier"
