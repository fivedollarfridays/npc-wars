"""Tests for engine/game.py — full match e2e with deterministic bots."""

from unittest.mock import patch

from tests.conftest import always_rest, bot_config, chase_and_attack

from engine.game import MAX_ROUNDS, run_match


def _always_move_south(state):
    return ("move", "south")


def _always_attack_south(state):
    return ("attack", "south")


class TestRunMatch:
    def test_returns_valid_match_data(self):
        configs = [
            bot_config("A", "🅰️", always_rest),
            bot_config("B", "🅱️", chase_and_attack),
        ]
        data = run_match(configs, match_id=1, seed=42)
        expected_keys = {
            "match_id", "date", "grid_size", "players", "rounds",
            "eliminations", "winner", "stats", "duration_rounds",
        }
        assert set(data.keys()) == expected_keys

    def test_match_id_passed_through(self):
        configs = [
            bot_config("A", "🅰️", always_rest),
            bot_config("B", "🅱️", always_rest),
        ]
        data = run_match(configs, match_id=99, seed=1)
        assert data["match_id"] == 99

    def test_deterministic_with_seed(self):
        configs = [
            bot_config("A", "🅰️", chase_and_attack),
            bot_config("B", "🅱️", chase_and_attack),
        ]
        data1 = run_match(configs, seed=42)
        data2 = run_match(configs, seed=42)
        assert data1["winner"] == data2["winner"]
        assert data1["duration_rounds"] == data2["duration_rounds"]
        assert len(data1["rounds"]) == len(data2["rounds"])

    def test_match_ends_with_winner(self):
        configs = [
            bot_config("Rest", "😴", always_rest),
            bot_config("Kill", "⚔️", chase_and_attack),
        ]
        data = run_match(configs, seed=42)
        assert data["winner"] in {"😴", "⚔️"}
        assert data["duration_rounds"] <= MAX_ROUNDS

    @patch("engine.game.get_storm_border", return_value=0)
    def test_200_round_cap(self, _mock_storm):
        """Two resting bots with no storm never kill each other — should hit cap."""
        configs = [
            bot_config("A", "🅰️", always_rest),
            bot_config("B", "🅱️", always_rest),
        ]
        data = run_match(configs, seed=1)
        assert data["duration_rounds"] == MAX_ROUNDS

    def test_stats_populated(self):
        configs = [
            bot_config("A", "🅰️", chase_and_attack),
            bot_config("B", "🅱️", always_rest),
        ]
        data = run_match(configs, seed=42)
        for emoji in ["🅰️", "🅱️"]:
            assert emoji in data["stats"]
            s = data["stats"][emoji]
            assert "kills" in s
            assert "damage_dealt" in s
            assert "damage_taken" in s
            assert "rounds_survived" in s

    def test_players_list_matches_input(self):
        configs = [
            bot_config("Alpha", "🅰️", always_rest),
            bot_config("Bravo", "🅱️", always_rest),
        ]
        data = run_match(configs, seed=1)
        assert len(data["players"]) == 2
        names = {p["name"] for p in data["players"]}
        assert names == {"Alpha", "Bravo"}

    def test_round_data_structure(self):
        configs = [
            bot_config("A", "🅰️", chase_and_attack),
            bot_config("B", "🅱️", chase_and_attack),
        ]
        data = run_match(configs, seed=42)
        rnd = data["rounds"][0]
        assert "round" in rnd
        assert "storm_border" in rnd
        assert "positions" in rnd
        assert "events" in rnd
        assert len(rnd["positions"]) == 2

    def test_storm_damage_in_late_rounds(self):
        """Bots that never move get caught by storm eventually."""
        configs = [
            bot_config("A", "🅰️", always_rest),
            bot_config("B", "🅱️", always_rest),
        ]
        data = run_match(configs, seed=42)
        storm_events = [
            e for rnd in data["rounds"] for e in rnd["events"]
            if e.get("type") == "storm_damage"
        ]
        assert len(storm_events) > 0

    def test_single_bot_match(self):
        """Single bot match ends immediately with that bot as winner."""
        configs = [
            bot_config("Solo", "\U0001f3af", always_rest),
        ]
        data = run_match(configs, seed=42)
        assert data["winner"] == "\U0001f3af"
        assert data["duration_rounds"] <= 1

    def test_disconnection_on_failures(self):
        """Bot returning invalid actions 3 times gets disconnected."""
        call_count = [0]

        def bad_bot(state):
            call_count[0] += 1
            return "invalid"  # Not a tuple

        configs = [
            bot_config("Bad", "💥", bad_bot),
            bot_config("Good", "✅", always_rest),
        ]
        data = run_match(configs, seed=42)
        assert data["winner"] == "✅"


class TestSpectacleMetadata:
    """Verify every round in match JSON includes spectacle data."""

    def test_every_round_has_spectacle_key(self):
        """Every round in match output must have a 'spectacle' key."""
        configs = [
            bot_config("A", "🅰️", chase_and_attack),
            bot_config("B", "🅱️", chase_and_attack),
        ]
        data = run_match(configs, seed=42)
        for i, rnd in enumerate(data["rounds"]):
            assert "spectacle" in rnd, f"Round {i} missing 'spectacle' key"

    def test_spectacle_has_required_fields(self):
        """Each spectacle object has drama_score (int), tier (str), triggers (list), effects (list)."""
        configs = [
            bot_config("A", "🅰️", chase_and_attack),
            bot_config("B", "🅱️", chase_and_attack),
        ]
        data = run_match(configs, seed=42)
        for i, rnd in enumerate(data["rounds"]):
            spec = rnd["spectacle"]
            assert isinstance(spec["drama_score"], int), f"Round {i}: drama_score not int"
            assert isinstance(spec["tier"], str), f"Round {i}: tier not str"
            assert isinstance(spec["triggers"], list), f"Round {i}: triggers not list"
            assert isinstance(spec["effects"], list), f"Round {i}: effects not list"

    def test_existing_round_fields_still_present(self):
        """Spectacle addition must not remove existing round fields."""
        configs = [
            bot_config("A", "🅰️", chase_and_attack),
            bot_config("B", "🅱️", chase_and_attack),
        ]
        data = run_match(configs, seed=42)
        for rnd in data["rounds"]:
            assert "round" in rnd
            assert "storm_border" in rnd
            assert "positions" in rnd
            assert "events" in rnd

    def test_calm_round_has_spectacle(self):
        """Even calm rounds (no combat) must have spectacle with drama_score=0, tier='calm'."""
        configs = [
            bot_config("A", "🅰️", always_rest),
            bot_config("B", "🅱️", always_rest),
        ]
        data = run_match(configs, seed=42)
        # Early rounds with resting bots should be calm
        first_round = data["rounds"][0]
        assert "spectacle" in first_round
        spec = first_round["spectacle"]
        assert spec["drama_score"] == 0
        assert spec["tier"] == "calm"
