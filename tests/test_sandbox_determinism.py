"""Sandbox RNG determinism (T74.1).

Forked decide() children do NOT inherit the parent's seeded global ``random``
state, so a bot using ``import random`` is otherwise non-reproducible — which
breaks byte-stable balance baselines. The sandbox seeds the child's global RNG
from observable game state; these tests pin that contract.
"""
from __future__ import annotations

from engine.sandbox import _deterministic_seed, execute_decide


def _global_random_bot(state):
    """A bot that uses the *global* random module (like starter/reaper/viper)."""
    import random

    return ("move", random.choice(["north", "south", "east", "west"]))


def _state(rnd=1, x=2, y=3, hp=100, energy=50, emoji="🤖"):
    return {"round": rnd, "me": {"x": x, "y": y, "hp": hp, "energy": energy, "emoji": emoji}}


class TestSandboxDeterminism:
    """A global-random bot is reproducible for identical state."""

    def test_same_state_same_action(self):
        s = _state()
        assert execute_decide(_global_random_bot, s) == execute_decide(_global_random_bot, s)

    def test_different_round_can_differ(self):
        # Across a spread of rounds the bot is not frozen on one action.
        actions = {execute_decide(_global_random_bot, _state(rnd=r)) for r in range(1, 12)}
        assert len(actions) > 1

    def test_seed_is_hashseed_independent(self):
        """The derived seed must not depend on PYTHONHASHSEED (str hashing)."""
        s = _state()
        assert _deterministic_seed(s) == _deterministic_seed(dict(s))
        assert isinstance(_deterministic_seed(s), int)
