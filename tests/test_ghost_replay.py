"""Tests for engine/ghost_replay.py — ghost replay alternate timeline."""

import copy

import pytest

from engine.game import run_match


def _make_config(emoji, decide_func):
    return {"name": emoji, "emoji": emoji, "bio": "", "author": "test",
            "decide_func": decide_func}


def _attacker(state):
    return ("attack", "north")


def _defender(state):
    return ("defend",)


@pytest.fixture()
def match_data():
    """Run a real 2-bot match for ghost replay tests."""
    configs = [
        _make_config("A", _attacker),
        _make_config("D", _defender),
    ]
    return run_match(configs, match_id=1, seed=42)


class TestGhostReplayBasics:
    """Core ghost replay functionality."""

    def test_returns_ghost_match_json(self, match_data):
        from engine.ghost_replay import ghost_replay
        result = ghost_replay(match_data, round_num=3, bot_emoji="A",
                              alt_action="defend", seed=42)
        assert isinstance(result, dict)
        assert "rounds" in result
        assert "winner" in result
        assert result["ghost"] is True

    def test_divergence_point_marked(self, match_data):
        from engine.ghost_replay import ghost_replay
        result = ghost_replay(match_data, round_num=3, bot_emoji="A",
                              alt_action="defend", seed=42)
        assert result["divergence_round"] == 3
        # The fork round itself should be flagged
        fork_round = result["rounds"][2]  # 0-indexed, round 3
        assert fork_round.get("divergence_point") is True

    def test_original_match_unmodified(self, match_data):
        from engine.ghost_replay import ghost_replay
        original = copy.deepcopy(match_data)
        ghost_replay(match_data, round_num=3, bot_emoji="A",
                     alt_action="defend", seed=42)
        assert match_data == original

    def test_same_seed_deterministic(self, match_data):
        from engine.ghost_replay import ghost_replay
        r1 = ghost_replay(match_data, round_num=3, bot_emoji="A",
                           alt_action="defend", seed=99)
        r2 = ghost_replay(match_data, round_num=3, bot_emoji="A",
                           alt_action="defend", seed=99)
        assert r1["rounds"] == r2["rounds"]
        assert r1["winner"] == r2["winner"]

    def test_rounds_before_fork_unchanged(self, match_data):
        from engine.ghost_replay import ghost_replay
        result = ghost_replay(match_data, round_num=5, bot_emoji="A",
                              alt_action="defend", seed=42)
        # Rounds 1-4 should be identical to original
        for i in range(4):
            assert result["rounds"][i] == match_data["rounds"][i]


class TestActionSubstitution:
    """Substituting attack→defend and other action swaps."""

    def test_substitute_attack_to_defend(self, match_data):
        from engine.ghost_replay import ghost_replay
        result = ghost_replay(match_data, round_num=3, bot_emoji="A",
                              alt_action="defend", seed=42)
        fork_round = result["rounds"][2]
        # Bot A should have defend action at the fork round
        a_pos = next(p for p in fork_round["positions"] if p["emoji"] == "A")
        assert a_pos["action"] == "defend"

    def test_substitute_defend_to_attack(self, match_data):
        from engine.ghost_replay import ghost_replay
        result = ghost_replay(match_data, round_num=3, bot_emoji="D",
                              alt_action="attack north", seed=42)
        fork_round = result["rounds"][2]
        d_pos = next(p for p in fork_round["positions"] if p["emoji"] == "D")
        assert d_pos["action"] == "attack north"


class TestDivergenceTiming:
    """Early and late divergence points."""

    def test_early_divergence_round_1(self, match_data):
        from engine.ghost_replay import ghost_replay
        result = ghost_replay(match_data, round_num=1, bot_emoji="A",
                              alt_action="defend", seed=42)
        assert result["divergence_round"] == 1
        assert len(result["rounds"]) >= 1
        assert result["rounds"][0].get("divergence_point") is True

    def test_late_divergence(self, match_data):
        from engine.ghost_replay import ghost_replay
        last_round = len(match_data["rounds"])
        result = ghost_replay(match_data, round_num=last_round,
                              bot_emoji="A", alt_action="rest", seed=42)
        assert result["divergence_round"] == last_round
        assert len(result["rounds"]) >= last_round

    def test_ghost_simulates_to_completion(self, match_data):
        from engine.ghost_replay import ghost_replay
        result = ghost_replay(match_data, round_num=2, bot_emoji="A",
                              alt_action="rest", seed=42)
        # Ghost should have a winner
        assert result["winner"] is not None
        # Should have original_winner for comparison
        assert result["original_winner"] == match_data["winner"]


class TestEdgeCases:
    """Validation and edge cases."""

    def test_invalid_round_raises(self, match_data):
        from engine.ghost_replay import ghost_replay
        with pytest.raises(ValueError):
            ghost_replay(match_data, round_num=0, bot_emoji="A",
                         alt_action="defend", seed=42)
        with pytest.raises(ValueError):
            ghost_replay(match_data, round_num=9999, bot_emoji="A",
                         alt_action="defend", seed=42)

    def test_file_under_200_loc(self):
        from pathlib import Path
        src = Path("engine/ghost_replay.py").read_text()
        lines = [ln for ln in src.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        assert len(lines) < 200
