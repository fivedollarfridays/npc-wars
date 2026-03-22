"""Sprint 37 regression tests for terrain balance across maps."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.terrain import MAP_NAMES

_RESULTS_PATH = Path("tools/terrain_balance_results.json")


@pytest.fixture()
def balance_results() -> dict:
    """Load terrain balance results, skip if not generated."""
    if not _RESULTS_PATH.exists():
        pytest.skip("terrain_balance_results.json not generated yet")
    return json.loads(_RESULTS_PATH.read_text())


def test_no_bot_over_65_on_any_map(balance_results: dict) -> None:
    """No bot should exceed 65% win rate on any single map."""
    for bot_name, data in balance_results.items():
        for map_name, stats in data.get("per_map", {}).items():
            rate = stats.get("win_rate", 0)
            assert rate <= 65.0, (
                f"{bot_name} has {rate}% win rate on {map_name} (max 65%)"
            )


def test_all_bots_have_min_games_per_map(balance_results: dict) -> None:
    """Every bot must have at least 10 games on each map."""
    for bot_name, data in balance_results.items():
        for map_name in MAP_NAMES:
            stats = data.get("per_map", {}).get(map_name, {})
            total = stats.get("total", 0)
            assert total >= 10, (
                f"{bot_name} only played {total} games on {map_name} (min 10)"
            )


def test_all_maps_represented(balance_results: dict) -> None:
    """Results should contain data for all 5 maps."""
    first_bot = next(iter(balance_results.values()))
    maps_in_results = set(first_bot.get("per_map", {}).keys())
    for m in MAP_NAMES:
        assert m in maps_in_results, f"Map {m} missing from results"
