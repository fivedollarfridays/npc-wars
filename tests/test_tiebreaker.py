"""Tests for 200-round tiebreaker — winner selected when cap is reached."""

from unittest.mock import patch

from tests.conftest import always_rest, bot_config

from engine.game import MAX_ROUNDS, run_match


class TestTiebreaker:
    @patch("engine.game.get_storm_border", return_value=0)
    def test_cap_reached_has_winner(self, _mock_storm):
        """Two resting bots with no storm reach 200 rounds — should have a winner."""
        configs = [
            bot_config("A", "🅰️", always_rest),
            bot_config("B", "🅱️", always_rest),
        ]
        data = run_match(configs, seed=1)
        assert data["duration_rounds"] == MAX_ROUNDS
        assert data["winner"] != "none"

    @patch("engine.game.get_storm_border", return_value=0)
    def test_tiebreaker_elimination_records(self, _mock_storm):
        """Losers in tiebreaker should have elimination records."""
        configs = [
            bot_config("A", "🅰️", always_rest),
            bot_config("B", "🅱️", always_rest),
        ]
        data = run_match(configs, seed=1)
        # One bot should be eliminated by tiebreaker
        tiebreaker_elims = [e for e in data["eliminations"] if e.get("cause") == "tiebreaker"]
        assert len(tiebreaker_elims) >= 1

    @patch("engine.game.get_storm_border", return_value=0)
    def test_tiebreaker_highest_hp_wins(self, _mock_storm):
        """Two resting bots with no storm reach MAX_ROUNDS; winner by tiebreaker."""
        configs = [
            bot_config("Rester", "😴", always_rest),
            bot_config("Chiller", "🛡️", always_rest),
        ]
        data = run_match(configs, seed=1)
        assert data["duration_rounds"] == MAX_ROUNDS
        assert data["winner"] in {"😴", "🛡️"}

    @patch("engine.game.get_storm_border", return_value=0)
    def test_three_bots_tiebreaker(self, _mock_storm):
        """Three resting bots with no storm — only one winner after tiebreaker."""
        configs = [
            bot_config("A", "🅰️", always_rest),
            bot_config("B", "🅱️", always_rest),
            bot_config("C", "🅾️", always_rest),
        ]
        data = run_match(configs, seed=42)
        assert data["winner"] in {"🅰️", "🅱️", "🅾️"}
        assert data["winner"] != "none"
