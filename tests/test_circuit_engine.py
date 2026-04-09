"""Tests for Code Circuit race engine (T66.1).

Verifies the minimal race engine produces valid race data
with TV-compatible output (commentary, highlights).
"""

from __future__ import annotations


class TestRunRace:
    """engine.circuit.run_race produces valid race data."""

    def test_run_race_returns_dict(self) -> None:
        from engine.circuit import run_race

        result = run_race(car_configs=_sample_cars(), laps=3, seed=42)
        assert isinstance(result, dict)

    def test_race_has_required_keys(self) -> None:
        from engine.circuit import run_race

        result = run_race(car_configs=_sample_cars(), laps=3, seed=42)
        for key in ("game", "cars", "laps", "results", "events", "rounds"):
            assert key in result, f"Missing key: {key}"

    def test_game_is_circuit(self) -> None:
        from engine.circuit import run_race

        result = run_race(car_configs=_sample_cars(), laps=3, seed=42)
        assert result["game"] == "circuit"

    def test_results_ordered_by_position(self) -> None:
        from engine.circuit import run_race

        result = run_race(car_configs=_sample_cars(), laps=3, seed=42)
        results = result["results"]
        assert len(results) >= 2
        positions = [r["position"] for r in results]
        assert positions == sorted(positions)

    def test_winner_is_position_one(self) -> None:
        from engine.circuit import run_race

        result = run_race(car_configs=_sample_cars(), laps=3, seed=42)
        assert result["winner"] == result["results"][0]["car"]

    def test_events_are_list(self) -> None:
        from engine.circuit import run_race

        result = run_race(car_configs=_sample_cars(), laps=3, seed=42)
        assert isinstance(result["events"], list)

    def test_deterministic_with_seed(self) -> None:
        from engine.circuit import run_race

        r1 = run_race(car_configs=_sample_cars(), laps=3, seed=42)
        r2 = run_race(car_configs=_sample_cars(), laps=3, seed=42)
        assert r1["results"] == r2["results"]

    def test_players_key_for_episode_compat(self) -> None:
        """Episode generator expects 'players' list."""
        from engine.circuit import run_race

        result = run_race(car_configs=_sample_cars(), laps=3, seed=42)
        assert "players" in result
        assert len(result["players"]) == len(_sample_cars())

    def test_rounds_have_positions(self) -> None:
        """Each round should have car positions for viewer rendering."""
        from engine.circuit import run_race

        result = run_race(car_configs=_sample_cars(), laps=3, seed=42)
        assert len(result["rounds"]) > 0
        for rnd in result["rounds"]:
            assert "positions" in rnd


class TestRaceTV:
    """Race engine produces TV-compatible output."""

    def test_enrich_tv_adds_commentary(self) -> None:
        from engine.circuit import run_race
        from engine.circuit_tv import enrich_circuit_tv

        race_data = run_race(car_configs=_sample_cars(), laps=3, seed=42)
        enrich_circuit_tv(race_data)
        assert "commentary" in race_data
        assert isinstance(race_data["commentary"], list)

    def test_enrich_tv_adds_highlights(self) -> None:
        from engine.circuit import run_race
        from engine.circuit_tv import enrich_circuit_tv

        race_data = run_race(car_configs=_sample_cars(), laps=3, seed=42)
        enrich_circuit_tv(race_data)
        assert "highlights" in race_data
        assert isinstance(race_data["highlights"], list)


def _sample_cars() -> list[dict]:
    return [
        {"name": "Speedster", "emoji": "🏎️", "strategy": "aggressive"},
        {"name": "Cruiser", "emoji": "🚗", "strategy": "conservative"},
        {"name": "Drifter", "emoji": "🏁", "strategy": "balanced"},
    ]
