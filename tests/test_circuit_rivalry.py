"""Tests for engine/circuit_rivalry.py — Code Circuit racing rivalry tracker."""

from engine.circuit_rivalry import compute_rivalry


def _race(cars, finish, overtakes=None, defends=None, laps_battling=0, points=None):
    """Build minimal race dict for rivalry tests."""
    return {
        "cars": cars,
        "finish": finish,  # {car: position}
        "overtakes": overtakes or [],
        "defends": defends or [],
        "laps_battling": laps_battling,
        "championship_points": points or {},
    }


# --- no history ---

class TestNoHistory:
    def test_empty_race_history(self):
        r = compute_rivalry("A", "B", [])
        assert r["races"] == 0
        assert r["rivalry_score"] == 0
        assert r["narrative_hooks"] == []

    def test_cars_never_raced_together(self):
        races = [_race(["A", "C"], {"A": 1, "C": 2})]
        r = compute_rivalry("A", "B", races)
        assert r["races"] == 0


# --- single race ---

class TestSingleRace:
    def test_basic_single_race(self):
        races = [_race(
            ["A", "B"], {"A": 1, "B": 2},
            overtakes=[{"overtaker": "A", "defender": "B", "lap": 5}],
            defends=[{"defender": "B", "attacker": "A", "lap": 8}],
            laps_battling=12,
            points={"A": 25, "B": 18},
        )]
        r = compute_rivalry("A", "B", races)
        assert r["races"] == 1
        assert r["overtakes_a"] == 1
        assert r["overtakes_b"] == 0
        assert r["defends_a"] == 0
        assert r["defends_b"] == 1
        assert r["laps_battling"] == 12
        assert r["points_a"] == 25
        assert r["points_b"] == 18
        assert 0 <= r["rivalry_score"] <= 100

    def test_no_overtakes(self):
        races = [_race(["A", "B"], {"A": 1, "B": 5}, laps_battling=0)]
        r = compute_rivalry("A", "B", races)
        assert r["overtakes_a"] == 0
        assert r["overtakes_b"] == 0
        assert r["rivalry_score"] < 20  # low competitiveness

    def test_narrative_hooks_present(self):
        races = [_race(
            ["A", "B"], {"A": 1, "B": 2},
            overtakes=[
                {"overtaker": "A", "defender": "B", "lap": 3},
                {"overtaker": "B", "defender": "A", "lap": 7},
            ],
            laps_battling=20,
        )]
        r = compute_rivalry("A", "B", races)
        assert isinstance(r["narrative_hooks"], list)
        assert len(r["narrative_hooks"]) > 0


# --- season-long rivalry ---

class TestSeasonRivalry:
    def test_multi_race_accumulation(self):
        races = [
            _race(["A", "B"], {"A": 1, "B": 2},
                   overtakes=[{"overtaker": "A", "defender": "B", "lap": 5}],
                   laps_battling=10, points={"A": 25, "B": 18}),
            _race(["A", "B"], {"A": 2, "B": 1},
                   overtakes=[{"overtaker": "B", "defender": "A", "lap": 3}],
                   laps_battling=15, points={"A": 18, "B": 25}),
            _race(["A", "B"], {"A": 1, "B": 2},
                   overtakes=[
                       {"overtaker": "A", "defender": "B", "lap": 10},
                       {"overtaker": "B", "defender": "A", "lap": 15},
                       {"overtaker": "A", "defender": "B", "lap": 20},
                   ],
                   defends=[{"defender": "A", "attacker": "B", "lap": 22}],
                   laps_battling=25, points={"A": 25, "B": 18}),
        ]
        r = compute_rivalry("A", "B", races)
        assert r["races"] == 3
        assert r["overtakes_a"] == 3
        assert r["overtakes_b"] == 2
        assert r["defends_a"] == 1
        assert r["laps_battling"] == 50
        assert r["points_a"] == 68
        assert r["points_b"] == 61

    def test_high_rivalry_score_for_close_battle(self):
        """Evenly matched cars with lots of overtakes = high score."""
        races = [
            _race(["A", "B"], {"A": 1, "B": 2},
                   overtakes=[
                       {"overtaker": "A", "defender": "B", "lap": i}
                       for i in range(5)
                   ] + [
                       {"overtaker": "B", "defender": "A", "lap": i}
                       for i in range(5, 10)
                   ],
                   laps_battling=30, points={"A": 25, "B": 18}),
            _race(["A", "B"], {"A": 2, "B": 1},
                   overtakes=[
                       {"overtaker": "B", "defender": "A", "lap": i}
                       for i in range(5)
                   ] + [
                       {"overtaker": "A", "defender": "B", "lap": i}
                       for i in range(5, 10)
                   ],
                   laps_battling=28, points={"A": 18, "B": 25}),
        ]
        r = compute_rivalry("A", "B", races)
        assert r["rivalry_score"] >= 70

    def test_low_rivalry_score_for_dominance(self):
        """One car always far ahead = low rivalry."""
        races = [
            _race(["A", "B"], {"A": 1, "B": 10}, laps_battling=0,
                   points={"A": 25, "B": 1}),
            _race(["A", "B"], {"A": 1, "B": 8}, laps_battling=0,
                   points={"A": 25, "B": 4}),
        ]
        r = compute_rivalry("A", "B", races)
        assert r["rivalry_score"] < 30

    def test_skips_races_without_both_cars(self):
        races = [
            _race(["A", "B"], {"A": 1, "B": 2}, laps_battling=5),
            _race(["A", "C"], {"A": 1, "C": 2}, laps_battling=10),
            _race(["A", "B"], {"A": 2, "B": 1}, laps_battling=8),
        ]
        r = compute_rivalry("A", "B", races)
        assert r["races"] == 2
        assert r["laps_battling"] == 13

    def test_narrative_hooks_for_season(self):
        races = [
            _race(["A", "B"], {"A": 1, "B": 2},
                   overtakes=[{"overtaker": "A", "defender": "B", "lap": 5}],
                   laps_battling=15, points={"A": 25, "B": 18}),
        ] * 5
        r = compute_rivalry("A", "B", races)
        hooks = r["narrative_hooks"]
        assert isinstance(hooks, list)
        assert len(hooks) >= 1
