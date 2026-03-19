"""Tests for T28.3: RNG threaded through game loop."""

import random

import pytest

from tests.conftest import bot_config, chase_and_attack, make_bot
from engine.game import _execute_round, _resolve_combat_phases, run_match


class TestExecuteRoundAcceptsRng:
    """_execute_round accepts and forwards rng parameter."""

    def test_execute_round_with_rng_param(self):
        """_execute_round can be called with an rng keyword argument."""
        rng = random.Random(42)
        grid_size = 10
        bots = [
            make_bot("A", "A1", x=1, y=1),
            make_bot("B", "B1", x=8, y=8),
        ]
        round_data, elims, bumps = _execute_round(
            bots, round_num=1, grid_size=grid_size, storm_border=0,
            rng=rng,
        )
        assert isinstance(round_data, dict)

    def test_execute_round_rng_default_none(self):
        """_execute_round still works without rng (backward compat)."""
        grid_size = 10
        bots = [
            make_bot("A", "A1", x=1, y=1),
            make_bot("B", "B1", x=8, y=8),
        ]
        round_data, elims, bumps = _execute_round(
            bots, round_num=1, grid_size=grid_size, storm_border=0,
        )
        assert isinstance(round_data, dict)


class TestResolveCombatPhasesAcceptsRng:
    """_resolve_combat_phases accepts rng parameter."""

    def test_resolve_combat_phases_with_rng(self):
        """_resolve_combat_phases can be called with rng keyword."""
        rng = random.Random(42)
        bots = [
            make_bot("A", "A1", x=1, y=1),
            make_bot("B", "B1", x=8, y=8),
        ]
        alive = [b for b in bots if b.alive]
        actions = {b.emoji: ("rest",) for b in alive}
        round_data, elims, bumps = _resolve_combat_phases(
            alive, bots, actions, forced_rest=set(), override_events=[],
            round_num=1, grid_size=10, storm_border=0,
            rng=rng,
        )
        assert isinstance(round_data, dict)


class TestAsyncRoundAcceptsRng:
    """_execute_round_async accepts rng parameter."""

    @pytest.mark.asyncio
    async def test_async_round_with_rng(self):
        """_execute_round_async can be called with rng keyword."""
        from engine.game_async import _execute_round_async

        rng = random.Random(42)
        bots = [
            make_bot("A", "A1", x=1, y=1),
            make_bot("B", "B1", x=8, y=8),
        ]
        round_data, elims, bumps, responded = await _execute_round_async(
            bots, round_num=1, grid_size=10, storm_border=0,
            rng=rng,
        )
        assert isinstance(round_data, dict)


class TestRunMatchDeterministic:
    """run_match remains deterministic after RNG threading refactor."""

    def test_same_seed_same_result(self):
        """Same seed produces identical match outcome."""
        configs = [
            bot_config("A", "A1", chase_and_attack),
            bot_config("B", "B1", chase_and_attack),
        ]
        data1 = run_match(configs, seed=99)
        data2 = run_match(configs, seed=99)
        assert data1["winner"] == data2["winner"]
        assert data1["duration_rounds"] == data2["duration_rounds"]
        assert len(data1["rounds"]) == len(data2["rounds"])
