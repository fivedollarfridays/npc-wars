"""Tests for tools/ability_balance_sim.py -- ability balance simulation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.ability_balance_sim import (
    build_mage_config,
    run_simulation,
)


class TestMageConfig:
    def test_config_has_required_keys(self) -> None:
        config = build_mage_config()
        for key in ("name", "emoji", "bio", "author", "decide_func"):
            assert key in config, f"Missing key: {key}"

    def test_config_decide_is_callable(self) -> None:
        config = build_mage_config()
        assert callable(config["decide_func"])

    def test_config_has_equipment(self) -> None:
        config = build_mage_config()
        assert "equipment" in config

    def test_config_has_callbacks(self) -> None:
        """Mage config should include callback functions for power_up and evolve."""
        config = build_mage_config()
        assert "callbacks" in config


class TestSimulation:
    def test_small_sim_runs(self) -> None:
        """Run a tiny sim (5 matches) to verify it works."""
        results = run_simulation(n_matches=5, seed_base=9000)
        assert isinstance(results, dict)
        assert len(results) > 0

    def test_results_have_win_rate(self) -> None:
        results = run_simulation(n_matches=5, seed_base=9001)
        for name, stats in results.items():
            if name.startswith("_"):
                continue
            assert "win_rate" in stats
            assert "total" in stats
            assert "wins" in stats
