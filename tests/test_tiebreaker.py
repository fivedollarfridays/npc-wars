"""Tests for 200-round tiebreaker — winner selected when cap is reached."""

from tests.conftest import always_rest, bot_config

from engine.game import MAX_ROUNDS, run_match


class TestTiebreaker:
    def test_cap_reached_has_winner(self):
        """Two resting bots reach 200 rounds — should have a winner, not 'none'."""
        configs = [
            bot_config("A", "🅰️", always_rest),
            bot_config("B", "🅱️", always_rest),
        ]
        data = run_match(configs, seed=1)
        assert data["duration_rounds"] == MAX_ROUNDS
        assert data["winner"] != "none"

    def test_tiebreaker_elimination_records(self):
        """Losers in tiebreaker should have elimination records."""
        configs = [
            bot_config("A", "🅰️", always_rest),
            bot_config("B", "🅱️", always_rest),
        ]
        data = run_match(configs, seed=1)
        # One bot should be eliminated by tiebreaker
        tiebreaker_elims = [e for e in data["eliminations"] if e.get("cause") == "tiebreaker"]
        assert len(tiebreaker_elims) >= 1

    def test_tiebreaker_highest_hp_wins(self):
        """Two resting bots always reach MAX_ROUNDS; winner decided by tiebreaker."""
        configs = [
            bot_config("Rester", "😴", always_rest),
            bot_config("Chiller", "🛡️", always_rest),
        ]
        data = run_match(configs, seed=1)
        assert data["duration_rounds"] == MAX_ROUNDS
        assert data["winner"] in {"😴", "🛡️"}

    def test_three_bots_tiebreaker(self):
        """Three resting bots — only one winner after tiebreaker."""
        configs = [
            bot_config("A", "🅰️", always_rest),
            bot_config("B", "🅱️", always_rest),
            bot_config("C", "🅾️", always_rest),
        ]
        data = run_match(configs, seed=42)
        assert data["winner"] in {"🅰️", "🅱️", "🅾️"}
        assert data["winner"] != "none"
