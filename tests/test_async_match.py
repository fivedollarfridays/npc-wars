"""Tests for async match execution with human input windows."""

import asyncio

import pytest

from tests.conftest import always_rest, bot_config, chase_and_attack, make_bot
from engine.game import run_match


# ---------------------------------------------------------------------------
# Cycle 1: Async match with 0 humans matches sync match (same seed)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_no_humans_matches_sync():
    """Async match with no human adapters produces identical results to sync."""
    from engine.game import run_match_async

    configs = [
        bot_config("A", "A1", chase_and_attack),
        bot_config("B", "B1", chase_and_attack),
    ]
    sync_data = run_match(configs, match_id=1, seed=42)
    async_data = await run_match_async(configs, match_id=1, seed=42)

    assert sync_data["winner"] == async_data["winner"]
    assert sync_data["duration_rounds"] == async_data["duration_rounds"]
    assert len(sync_data["rounds"]) == len(async_data["rounds"])


@pytest.mark.asyncio
async def test_async_returns_valid_match_data():
    """Async match returns the same match data structure as sync."""
    from engine.game import run_match_async

    configs = [
        bot_config("A", "A1", always_rest),
        bot_config("B", "B1", chase_and_attack),
    ]
    data = await run_match_async(configs, match_id=1, seed=42)

    expected_keys = {
        "match_id", "date", "grid_size", "players", "rounds",
        "eliminations", "winner", "stats", "duration_rounds", "match_mode",
    }
    assert set(data.keys()) == expected_keys


# ---------------------------------------------------------------------------
# Cycle 2: Human override works in async path
# ---------------------------------------------------------------------------


class AsyncMockAdapter:
    """Mock adapter with async get_action_async for testing."""

    def __init__(self, actions: list[tuple[str, ...] | None]) -> None:
        self._actions = list(actions)
        self._index = 0
        self.call_count = 0

    def get_action(self, state, timeout_s):
        """Sync fallback -- returns None so bot decide is used."""
        return None

    async def get_action_async(self, state, timeout_s):
        """Async version returns pre-configured actions."""
        self.call_count += 1
        if self._index >= len(self._actions):
            return None
        action = self._actions[self._index]
        self._index += 1
        return action


@pytest.mark.asyncio
async def test_async_round_uses_human_override():
    """_execute_round_async applies human override from get_action_async."""
    from engine.game import _execute_round_async

    adapter = AsyncMockAdapter([("attack", "north")])
    bot_h = make_bot(name="Human", emoji="HU", x=3, y=3)
    bot_h.human_adapter = adapter

    bot_a = make_bot(name="AI", emoji="AI", x=7, y=7)

    bots = [bot_h, bot_a]
    round_data, _, _, _ = await _execute_round_async(
        bots, round_num=1, grid_size=10, storm_border=0,
    )

    # Human bot should have used "attack north" instead of default "rest"
    positions = {p["emoji"]: p for p in round_data["positions"]}
    assert positions["HU"]["action"] == "attack north"
    assert positions["AI"]["action"] == "rest"
    assert adapter.call_count == 1


# ---------------------------------------------------------------------------
# Cycle 3: Bot fallback when human times out in async path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_timeout_falls_back_to_bot():
    """When async adapter returns None (timeout), bot's decide() is used."""
    from engine.game import _execute_round_async

    adapter = AsyncMockAdapter([None])  # simulate timeout
    bot_h = make_bot(name="Human", emoji="HU", x=3, y=3)
    bot_h.human_adapter = adapter

    bots = [bot_h, make_bot(name="AI", emoji="AI", x=7, y=7)]
    round_data, _, _, _ = await _execute_round_async(
        bots, round_num=1, grid_size=10, storm_border=0,
    )

    positions = {p["emoji"]: p for p in round_data["positions"]}
    # Bot's default decide_func returns ("rest",)
    assert positions["HU"]["action"] == "rest"


@pytest.mark.asyncio
async def test_async_real_timeout_falls_back():
    """When get_action_async takes too long, asyncio.TimeoutError triggers fallback."""
    from engine.game import _execute_round_async

    class SlowAdapter:
        async def get_action_async(self, state, timeout_s):
            await asyncio.sleep(10)  # way longer than timeout
            return ("attack", "north")

        def get_action(self, state, timeout_s):
            return None

    bot_h = make_bot(name="Slow", emoji="SL", x=3, y=3)
    bot_h.human_adapter = SlowAdapter()

    bots = [bot_h, make_bot(name="AI", emoji="AI", x=7, y=7)]
    round_data, _, _, _ = await _execute_round_async(
        bots, round_num=1, grid_size=10, storm_border=0,
        human_timeout=0.05,  # 50ms timeout
    )

    positions = {p["emoji"]: p for p in round_data["positions"]}
    assert positions["SL"]["action"] == "rest"  # fallback to bot decide


# ---------------------------------------------------------------------------
# Cycle 4: Multiple humans input simultaneously
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_multiple_humans_concurrent():
    """Multiple human adapters are gathered concurrently via asyncio.gather."""
    from engine.game import _execute_round_async

    call_order: list[str] = []

    class TrackingAdapter:
        def __init__(self, emoji: str, action: tuple[str, ...] | None):
            self._emoji = emoji
            self._action = action

        def get_action(self, state, timeout_s):
            return None

        async def get_action_async(self, state, timeout_s):
            call_order.append(self._emoji)
            await asyncio.sleep(0.01)  # simulate small delay
            return self._action

    bot_a = make_bot(name="H1", emoji="H1", x=2, y=2)
    bot_a.human_adapter = TrackingAdapter("H1", ("attack", "east"))

    bot_b = make_bot(name="H2", emoji="H2", x=7, y=7)
    bot_b.human_adapter = TrackingAdapter("H2", ("move", "north"))

    bot_c = make_bot(name="AI", emoji="AI", x=5, y=5)
    # No adapter on bot_c

    bots = [bot_a, bot_b, bot_c]
    round_data, _, _, _ = await _execute_round_async(
        bots, round_num=1, grid_size=10, storm_border=0,
    )

    positions = {p["emoji"]: p for p in round_data["positions"]}
    assert positions["H1"]["action"] == "attack east"
    assert positions["H2"]["action"] == "move north"
    assert positions["AI"]["action"] == "rest"
    # Both humans were called
    assert "H1" in call_order
    assert "H2" in call_order


# ---------------------------------------------------------------------------
# Cycle 5: Full async match with mix of responding/timing-out humans
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_match_completes_with_humans():
    """Full async match runs to completion with human adapters attached."""
    from engine.game import run_match_async

    configs = [
        bot_config("Human", "HU", always_rest),
        bot_config("Killer", "KI", chase_and_attack),
    ]

    data = await run_match_async(configs, match_id=1, seed=42)

    assert data["winner"] in {"HU", "KI"}
    assert data["duration_rounds"] > 0


@pytest.mark.asyncio
async def test_async_match_mixed_timeout_and_respond():
    """Async round handles mix: one human responds, one times out."""
    from engine.game import _execute_round_async

    respond_adapter = AsyncMockAdapter([("attack", "south")])
    timeout_adapter = AsyncMockAdapter([None])  # timeout

    bot_respond = make_bot(name="Respond", emoji="RE", x=3, y=3)
    bot_respond.human_adapter = respond_adapter

    bot_timeout = make_bot(name="Timeout", emoji="TO", x=7, y=7)
    bot_timeout.human_adapter = timeout_adapter

    bots = [bot_respond, bot_timeout]
    round_data, _, _, _ = await _execute_round_async(
        bots, round_num=1, grid_size=10, storm_border=0,
    )

    positions = {p["emoji"]: p for p in round_data["positions"]}
    assert positions["RE"]["action"] == "attack south"
    assert positions["TO"]["action"] == "rest"  # fallback to bot decide
