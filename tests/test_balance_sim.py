"""Tests for tools/balance_sim.py — archetype round-robin balance simulation."""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.balance_sim import (
    ARCHETYPES,
    _simple_decide,
    make_bot_config,
    run_simulation,
)


class TestArchetypes:
    """Validate archetype stat allocations."""

    def test_archetypes_sum_to_100(self) -> None:
        for name, alloc in ARCHETYPES.items():
            total = alloc.power + alloc.speed + alloc.armor + alloc.mind
            assert total == 100, f"{name} sums to {total}, expected 100"

    def test_archetypes_above_minimum(self) -> None:
        for name, alloc in ARCHETYPES.items():
            for stat_name in ("power", "speed", "armor", "mind"):
                val = getattr(alloc, stat_name)
                assert val >= 5, f"{name}.{stat_name} = {val}, must be >= 5"

    def test_seven_archetypes_defined(self) -> None:
        assert len(ARCHETYPES) == 7


class TestSimpleDecide:
    """Validate the simple bot AI returns valid actions."""

    def test_returns_rest_when_low_energy(self) -> None:
        state = {
            "me": {"x": 5, "y": 5, "energy": 3},
            "enemies": [{"x": 7, "y": 5}],
        }
        result = _simple_decide(state)
        assert result == ("rest",)

    def test_returns_attack_when_adjacent(self) -> None:
        state = {
            "me": {"x": 5, "y": 5, "energy": 50},
            "enemies": [{"x": 6, "y": 5}],
        }
        result = _simple_decide(state)
        assert result[0] == "attack"
        assert result[1] in ("north", "south", "east", "west")

    def test_returns_move_when_distant(self) -> None:
        state = {
            "me": {"x": 0, "y": 0, "energy": 50},
            "enemies": [{"x": 5, "y": 5}],
        }
        result = _simple_decide(state)
        assert result[0] == "move"
        assert result[1] in ("north", "south", "east", "west")

    def test_returns_rest_when_no_enemies(self) -> None:
        state = {"me": {"x": 5, "y": 5, "energy": 50}, "enemies": []}
        result = _simple_decide(state)
        assert result == ("rest",)


class TestMakeBotConfig:
    """Validate bot config has required fields."""

    def test_has_required_fields(self) -> None:
        alloc = ARCHETYPES["Balanced"]
        config = make_bot_config("TestBot", "X", alloc)
        required = {"name", "emoji", "bio", "author", "decide_func", "stat_allocation"}
        assert required.issubset(config.keys())

    def test_decide_func_is_callable(self) -> None:
        alloc = ARCHETYPES["Balanced"]
        config = make_bot_config("TestBot", "X", alloc)
        assert callable(config["decide_func"])


class TestRunSimulation:
    """Integration tests — use matches_per_combo=2 to keep fast."""

    def test_produces_results_for_all_archetypes(self) -> None:
        results = run_simulation(matches_per_combo=2, seed_base=42)
        assert set(results.keys()) == set(ARCHETYPES.keys())

    def test_all_archetypes_have_matches(self) -> None:
        results = run_simulation(matches_per_combo=2, seed_base=42)
        for name, data in results.items():
            assert data["total"] > 0, f"{name} has 0 total matches"

    def test_result_fields(self) -> None:
        results = run_simulation(matches_per_combo=2, seed_base=42)
        for name, data in results.items():
            assert "wins" in data
            assert "total" in data
            assert "win_rate" in data
            assert isinstance(data["win_rate"], float)
