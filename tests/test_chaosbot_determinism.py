"""Tests for ChaosBot determinism — same state produces same action."""

from bots.example_random import decide


class TestChaosBotDeterminism:
    def _make_state(self, round_num=1, x=5, y=5):
        return {
            "me": {"x": x, "y": y, "hp": 100, "energy": 100, "attack_power": 15, "defense": 0},
            "enemies": [],
            "round": round_num,
            "grid_size": 10,
            "storm_border": 0,
        }

    def test_same_state_same_action(self):
        state = self._make_state()
        action1 = decide(state)
        action2 = decide(state)
        assert action1 == action2

    def test_different_rounds_may_differ(self):
        """Different rounds can produce different actions (not guaranteed but likely)."""
        actions = set()
        for r in range(1, 50):
            state = self._make_state(round_num=r)
            actions.add(str(decide(state)))
        # With 49 different rounds, should get more than 1 unique action
        assert len(actions) > 1

    def test_deterministic_across_calls(self):
        """Multiple calls with varying states, replayed, produce identical sequence."""
        seq1 = []
        for r in range(1, 20):
            state = self._make_state(round_num=r, x=r % 10, y=r % 8)
            seq1.append(decide(state))

        seq2 = []
        for r in range(1, 20):
            state = self._make_state(round_num=r, x=r % 10, y=r % 8)
            seq2.append(decide(state))

        assert seq1 == seq2

    def test_returns_valid_action(self):
        state = self._make_state()
        action = decide(state)
        assert isinstance(action, tuple)
        assert action[0] in ("move", "attack", "rest", "defend")
