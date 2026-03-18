"""Tests for agentgrounds wars analyze — heatmap + analysis generator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _make_match(
    match_id: int,
    grid_size: int,
    players: list[dict],
    rounds: list[dict],
    eliminations: list[dict],
    winner: str,
    duration_rounds: int,
    stats: dict | None = None,
) -> dict:
    """Build a minimal valid match JSON matching the real format."""
    return {
        "match_id": match_id,
        "date": "2026-01-01T00:00:00+00:00",
        "grid_size": grid_size,
        "players": players,
        "rounds": rounds,
        "eliminations": eliminations,
        "winner": winner,
        "stats": stats or {},
        "duration_rounds": duration_rounds,
    }


def _two_bot_players() -> list[dict]:
    return [
        {"emoji": "A", "name": "AlphaBot", "bio": "a", "author": "test"},
        {"emoji": "B", "name": "BetaBot", "bio": "b", "author": "test"},
    ]


def _simple_rounds(grid_size: int = 10) -> list[dict]:
    """3-round match: A kills B on round 3 at position (2,3)."""
    return [
        {
            "round": 1,
            "storm_border": 0,
            "positions": [
                {"emoji": "A", "x": 1, "y": 1, "hp": 100, "energy": 90, "action": "move east", "alive": True},
                {"emoji": "B", "x": 5, "y": 5, "hp": 100, "energy": 90, "action": "move west", "alive": True},
            ],
            "events": [],
        },
        {
            "round": 2,
            "storm_border": 0,
            "positions": [
                {"emoji": "A", "x": 2, "y": 2, "hp": 100, "energy": 80, "action": "attack east", "alive": True},
                {"emoji": "B", "x": 3, "y": 3, "hp": 50, "energy": 80, "action": "move west", "alive": True},
            ],
            "events": [
                {"type": "hit", "attacker": "A", "target": "B", "damage": 50, "hp_before": 100},
            ],
        },
        {
            "round": 3,
            "storm_border": 0,
            "positions": [
                {"emoji": "A", "x": 2, "y": 3, "hp": 100, "energy": 70, "action": "attack east", "alive": True},
                {"emoji": "B", "x": 3, "y": 3, "hp": 0, "energy": 70, "action": "dead", "alive": False},
            ],
            "events": [
                {"type": "hit", "attacker": "A", "target": "B", "damage": 50, "hp_before": 50},
                {"type": "kill", "attacker": "A", "victim": "B", "round": 3},
            ],
        },
    ]


def _write_matches(tmp_path: Path, matches: list[dict]) -> Path:
    """Write match JSON files to tmp_path and return the directory."""
    for m in matches:
        path = tmp_path / f"match_{m['match_id']:03d}.json"
        path.write_text(json.dumps(m))
    return tmp_path


@pytest.fixture()
def sim_dir(tmp_path: Path) -> Path:
    """Create a sim output dir with 2 simple matches."""
    players = _two_bot_players()
    rounds = _simple_rounds()
    elims = [{"emoji": "B", "round": 3, "killed_by": "A", "cause": "combat"}]
    stats = {
        "A": {"kills": 1, "damage_dealt": 100, "damage_taken": 0, "rounds_survived": 3},
        "B": {"kills": 0, "damage_dealt": 0, "damage_taken": 100, "rounds_survived": 2},
    }
    m1 = _make_match(1, 10, players, rounds, elims, winner="A", duration_rounds=3, stats=stats)
    m2 = _make_match(2, 10, players, rounds, elims, winner="A", duration_rounds=3, stats=stats)
    return _write_matches(tmp_path, [m1, m2])


# ---------------------------------------------------------------------------
# Cycle 1: Parse matches and extract grid
# ---------------------------------------------------------------------------

class TestParseMatches:
    def test_load_matches_returns_list(self, sim_dir: Path) -> None:
        from agentgrounds.wars.analyzer import load_matches

        matches = load_matches(sim_dir)
        assert isinstance(matches, list)
        assert len(matches) == 2

    def test_detect_grid_size(self, sim_dir: Path) -> None:
        from agentgrounds.wars.analyzer import load_matches, detect_grid_size

        matches = load_matches(sim_dir)
        assert detect_grid_size(matches) == 10


# ---------------------------------------------------------------------------
# Cycle 2: Kill / death / balance heatmaps
# ---------------------------------------------------------------------------

class TestHeatmaps:
    def test_kill_heatmap_is_grid(self, sim_dir: Path) -> None:
        from agentgrounds.wars.analyzer import load_matches, build_heatmaps

        matches = load_matches(sim_dir)
        heatmaps = build_heatmaps(matches, grid_size=10)
        kill = heatmaps["kill"]
        assert len(kill) == 10
        assert all(len(row) == 10 for row in kill)

    def test_kill_heatmap_has_kills_at_victim_position(self, sim_dir: Path) -> None:
        from agentgrounds.wars.analyzer import load_matches, build_heatmaps

        matches = load_matches(sim_dir)
        heatmaps = build_heatmaps(matches, grid_size=10)
        # A (attacker) is at (2, 3) when kill happens — 2 matches
        assert heatmaps["kill"][3][2] == 2

    def test_death_heatmap_counts_deaths(self, sim_dir: Path) -> None:
        from agentgrounds.wars.analyzer import load_matches, build_heatmaps

        matches = load_matches(sim_dir)
        heatmaps = build_heatmaps(matches, grid_size=10)
        # B (victim) dies at (3, 3) — 2 matches
        assert heatmaps["death"][3][3] == 2

    def test_balance_map_is_kill_minus_death(self, sim_dir: Path) -> None:
        from agentgrounds.wars.analyzer import load_matches, build_heatmaps

        matches = load_matches(sim_dir)
        heatmaps = build_heatmaps(matches, grid_size=10)
        balance = heatmaps["balance"]
        assert len(balance) == 10
        assert all(len(row) == 10 for row in balance)
        # At (2,3) where A stood during the kill: kill=2, death=0 => balance=2
        assert balance[3][2] == 2
        # At (3,3) where B died: kill=0, death=2 => balance=-2
        assert balance[3][3] == -2


# ---------------------------------------------------------------------------
# Cycle 3: Energy curves by placement tier
# ---------------------------------------------------------------------------

class TestEnergyCurves:
    def test_energy_curves_has_placement_keys(self, sim_dir: Path) -> None:
        from agentgrounds.wars.analyzer import load_matches, build_energy_curves

        matches = load_matches(sim_dir)
        curves = build_energy_curves(matches)
        assert "placement_1" in curves
        assert "placement_2_3" in curves

    def test_energy_curves_values_are_lists(self, sim_dir: Path) -> None:
        from agentgrounds.wars.analyzer import load_matches, build_energy_curves

        matches = load_matches(sim_dir)
        curves = build_energy_curves(matches)
        for key in curves:
            assert isinstance(curves[key], list)
            assert len(curves[key]) > 0


# ---------------------------------------------------------------------------
# Cycle 4: ASCII heatmap rendering
# ---------------------------------------------------------------------------

class TestAsciiHeatmap:
    def test_ascii_heatmap_correct_dimensions(self) -> None:
        from agentgrounds.wars.analyzer import render_ascii_heatmap

        grid = [[0] * 10 for _ in range(10)]
        grid[5][5] = 10
        lines = render_ascii_heatmap(grid, title="Test")
        # Title line + 10 grid rows
        data_lines = [line for line in lines.strip().split("\n") if line.strip()]
        assert len(data_lines) >= 10  # at least 10 rows of grid

    def test_ascii_uses_intensity_chars(self) -> None:
        from agentgrounds.wars.analyzer import render_ascii_heatmap

        grid = [[0] * 10 for _ in range(10)]
        grid[0][0] = 100  # max intensity
        text = render_ascii_heatmap(grid, title="X")
        # Should contain at least the block char for max
        assert any(c in text for c in "\u2591\u2592\u2593\u2588")


# ---------------------------------------------------------------------------
# Cycle 5: Balance verdict
# ---------------------------------------------------------------------------

class TestBalanceVerdict:
    def test_verdict_keys(self, sim_dir: Path) -> None:
        from agentgrounds.wars.analyzer import load_matches, build_balance_verdict

        matches = load_matches(sim_dir)
        verdict = build_balance_verdict(matches)
        assert "match_length" in verdict
        assert "win_rate_spread" in verdict

    def test_verdict_values_are_pass_warn_fail(self, sim_dir: Path) -> None:
        from agentgrounds.wars.analyzer import load_matches, build_balance_verdict

        matches = load_matches(sim_dir)
        verdict = build_balance_verdict(matches)
        valid = {"PASS", "WARN", "FAIL"}
        for key, val in verdict.items():
            assert val["verdict"] in valid, f"{key} verdict={val['verdict']}"


# ---------------------------------------------------------------------------
# Cycle 6: Full analyze run writes output files
# ---------------------------------------------------------------------------

class TestAnalyzeRun:
    def test_analyze_writes_heatmaps_json(self, sim_dir: Path, tmp_path: Path) -> None:
        from agentgrounds.wars.analyzer import run_analysis

        out_dir = tmp_path / "analysis"
        run_analysis(input_dir=sim_dir, output_dir=out_dir, fmt="both")
        heatmaps = json.loads((out_dir / "heatmaps.json").read_text())
        assert "kill" in heatmaps
        assert "death" in heatmaps
        assert "balance" in heatmaps

    def test_analyze_writes_energy_curves(self, sim_dir: Path, tmp_path: Path) -> None:
        from agentgrounds.wars.analyzer import run_analysis

        out_dir = tmp_path / "analysis"
        run_analysis(input_dir=sim_dir, output_dir=out_dir, fmt="json")
        curves = json.loads((out_dir / "energy_curves.json").read_text())
        assert "placement_1" in curves

    def test_analyze_writes_report(self, sim_dir: Path, tmp_path: Path) -> None:
        from agentgrounds.wars.analyzer import run_analysis

        out_dir = tmp_path / "analysis"
        run_analysis(input_dir=sim_dir, output_dir=out_dir, fmt="json")
        report = json.loads((out_dir / "analysis_report.json").read_text())
        assert "verdict" in report
        assert "match_length" in report["verdict"]


# ---------------------------------------------------------------------------
# Cycle 7: CLI integration
# ---------------------------------------------------------------------------

class TestCLIIntegration:
    def test_analyze_cli_exits_zero(self, sim_dir: Path, tmp_path: Path) -> None:
        from agentgrounds.wars.cli import main

        out_dir = tmp_path / "cli_out"
        main(["analyze", "--input", str(sim_dir), "--output", str(out_dir), "--format", "both"])
        assert (out_dir / "heatmaps.json").exists()
        assert (out_dir / "energy_curves.json").exists()
        assert (out_dir / "analysis_report.json").exists()
