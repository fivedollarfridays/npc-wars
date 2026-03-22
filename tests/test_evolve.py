"""Tests for the evolve callback -- mid-match adaptation (T36.3)."""

from __future__ import annotations

from typing import Any

from engine.abilities import AbilityDef
from engine.callback_runner import check_evolve_trigger, run_evolve_callbacks
from engine.callbacks import CALLBACK_NAMES, CallbackSet
from engine.combat import Bot


def _make_bot(**overrides: Any) -> Bot:
    """Create a minimal bot for testing."""
    defaults: dict[str, Any] = {
        "name": "TestBot",
        "emoji": "T",
        "bio": "test",
        "author": "tester",
        "decide_func": lambda state: ("rest",),
        "x": 5,
        "y": 5,
    }
    defaults.update(overrides)
    return Bot(**defaults)


def _make_evolve_bot(
    evolve_fn: Any, kills: int = 3,
) -> tuple[Bot, list[Bot]]:
    """Create a bot with evolve callback and trigger condition met."""
    bot = _make_bot()
    bot.kills = kills
    bot.callbacks = CallbackSet(evolve=evolve_fn)
    return bot, [bot]


# --- Cycle 1: CALLBACK_NAMES + CallbackSet + has_evolved field ---

def test_evolve_in_callback_names() -> None:
    """'evolve' should be in the CALLBACK_NAMES tuple."""
    assert "evolve" in CALLBACK_NAMES


def test_callback_set_has_evolve_field() -> None:
    """CallbackSet should have an evolve field, default None."""
    cs = CallbackSet()
    assert cs.evolve is None


def test_callback_set_accepts_evolve() -> None:
    """CallbackSet should accept an evolve callable."""
    def _fn(state: Any) -> dict[str, Any]:
        return {}
    cs = CallbackSet(evolve=_fn)
    assert cs.evolve is _fn


def test_bot_has_evolved_field() -> None:
    """Bot should have a has_evolved field, default False."""
    bot = _make_bot()
    assert bot.has_evolved is False


# --- Cycle 2: check_evolve_trigger ---


def test_trigger_at_3_kills() -> None:
    """Trigger fires when bot has 3+ kills."""
    bot = _make_bot()
    bot.kills = 3
    assert check_evolve_trigger(bot, round_num=5) is True


def test_trigger_at_round_20() -> None:
    """Trigger fires at round 20 regardless of kills."""
    bot = _make_bot()
    bot.kills = 0
    assert check_evolve_trigger(bot, round_num=20) is True


def test_no_trigger_below_thresholds() -> None:
    """No trigger when kills < 3 and round < 20."""
    bot = _make_bot()
    bot.kills = 2
    assert check_evolve_trigger(bot, round_num=19) is False


def test_trigger_at_2_kills_round_20() -> None:
    """Round 20 triggers even with fewer than 3 kills."""
    bot = _make_bot()
    bot.kills = 1
    assert check_evolve_trigger(bot, round_num=20) is True


# --- Cycle 3: run_evolve_callbacks with validation ---


def test_evolve_applies_stat_shift() -> None:
    """Valid stat_shift (sums to 0) should modify bot stats."""
    def evolve_fn(state: Any) -> dict[str, Any]:
        return {"stat_shift": {"power": 5, "speed": -5}}

    bot, bots = _make_evolve_bot(evolve_fn)
    original_power = bot.stats.power
    original_speed = bot.stats.speed
    events = run_evolve_callbacks(bots, round_num=5, grid_size=10, storm_border=0)
    assert bot.stats.power == original_power + 5
    assert bot.stats.speed == original_speed - 5
    assert bot.has_evolved is True
    assert len(events) > 0


def test_evolve_applies_ability_boost() -> None:
    """Valid ability_boost should increase ability potency."""
    def evolve_fn(state: Any) -> dict[str, Any]:
        return {"ability_boost": 10}

    bot, bots = _make_evolve_bot(evolve_fn)
    bot.ability = AbilityDef(
        name="Fireball", type="damage", potency=20,
        range=2, cooldown=3, energy_cost=15,
    )
    run_evolve_callbacks(bots, round_num=5, grid_size=10, storm_border=0)
    assert bot.ability.potency == 30  # 20 + 10
    assert bot.has_evolved is True


def test_evolve_ability_boost_capped_at_15() -> None:
    """Ability boost above 15 should be capped."""
    def evolve_fn(state: Any) -> dict[str, Any]:
        return {"ability_boost": 20}

    bot, bots = _make_evolve_bot(evolve_fn)
    bot.ability = AbilityDef(
        name="Fireball", type="damage", potency=20,
        range=2, cooldown=3, energy_cost=15,
    )
    run_evolve_callbacks(bots, round_num=5, grid_size=10, storm_border=0)
    assert bot.ability.potency == 35  # 20 + 15 (capped)


def test_evolve_stat_shift_must_sum_to_zero() -> None:
    """Stat shift that doesn't sum to 0 should be ignored."""
    def evolve_fn(state: Any) -> dict[str, Any]:
        return {"stat_shift": {"power": 10, "speed": 0}}

    bot, bots = _make_evolve_bot(evolve_fn)
    original_power = bot.stats.power
    run_evolve_callbacks(bots, round_num=5, grid_size=10, storm_border=0)
    assert bot.stats.power == original_power  # not applied


def test_evolve_stat_shift_abs_over_10_ignored() -> None:
    """Individual stat shifts > abs(10) should be ignored."""
    def evolve_fn(state: Any) -> dict[str, Any]:
        return {"stat_shift": {"power": 15, "speed": -15}}

    bot, bots = _make_evolve_bot(evolve_fn)
    original_power = bot.stats.power
    run_evolve_callbacks(bots, round_num=5, grid_size=10, storm_border=0)
    assert bot.stats.power == original_power  # not applied


def test_evolve_only_fires_once() -> None:
    """Bot that already evolved should not evolve again."""
    call_count = 0
    def evolve_fn(state: Any) -> dict[str, Any]:
        nonlocal call_count
        call_count += 1
        return {"ability_boost": 5}

    bot, bots = _make_evolve_bot(evolve_fn)
    run_evolve_callbacks(bots, round_num=5, grid_size=10, storm_border=0)
    run_evolve_callbacks(bots, round_num=6, grid_size=10, storm_border=0)
    assert call_count == 1


def test_evolve_no_callback_no_event() -> None:
    """Bot without evolve callback produces no events."""
    bot = _make_bot()
    bot.kills = 5
    events = run_evolve_callbacks([bot], round_num=5, grid_size=10, storm_border=0)
    assert events == []


def test_evolve_not_triggered_no_event() -> None:
    """Bot with evolve callback but trigger not met produces no events."""
    def evolve_fn(state: Any) -> dict[str, Any]:
        return {"ability_boost": 5}

    bot = _make_bot()
    bot.kills = 0
    bot.callbacks = CallbackSet(evolve=evolve_fn)
    events = run_evolve_callbacks([bot], round_num=5, grid_size=10, storm_border=0)
    assert events == []
    assert bot.has_evolved is False


# --- Cycle 4: event structure + edge cases ---


def test_evolve_event_has_type_and_emoji() -> None:
    """Evolve event should contain type='evolve' and bot emoji."""
    def evolve_fn(state: Any) -> dict[str, Any]:
        return {"stat_shift": {"power": 5, "speed": -5}}

    bot, bots = _make_evolve_bot(evolve_fn)
    events = run_evolve_callbacks(bots, round_num=5, grid_size=10, storm_border=0)
    assert len(events) == 1
    assert events[0]["type"] == "evolve"
    assert events[0]["emoji"] == "T"
    assert events[0]["stat_shift"] == {"power": 5, "speed": -5}


def test_evolve_event_with_ability_boost() -> None:
    """Evolve event should report capped ability_boost."""
    def evolve_fn(state: Any) -> dict[str, Any]:
        return {"ability_boost": 10}

    bot, bots = _make_evolve_bot(evolve_fn)
    bot.ability = AbilityDef(
        name="Heal", type="heal", potency=15,
        range=0, cooldown=3, energy_cost=10,
    )
    events = run_evolve_callbacks(bots, round_num=5, grid_size=10, storm_border=0)
    assert events[0]["ability_boost"] == 10


def test_evolve_callback_exception_still_marks_evolved() -> None:
    """If evolve callback raises, bot is still marked as evolved."""
    def evolve_fn(state: Any) -> dict[str, Any]:
        raise RuntimeError("oops")

    bot, bots = _make_evolve_bot(evolve_fn)
    events = run_evolve_callbacks(bots, round_num=5, grid_size=10, storm_border=0)
    assert bot.has_evolved is True
    assert events == []


def test_evolve_dead_bot_skipped() -> None:
    """Dead bots should not evolve."""
    def evolve_fn(state: Any) -> dict[str, Any]:
        return {"ability_boost": 5}

    bot, bots = _make_evolve_bot(evolve_fn)
    bot.alive = False
    events = run_evolve_callbacks(bots, round_num=5, grid_size=10, storm_border=0)
    assert events == []
    assert bot.has_evolved is False


def test_evolve_both_stat_shift_and_ability_boost() -> None:
    """Both stat_shift and ability_boost can be applied together."""
    def evolve_fn(state: Any) -> dict[str, Any]:
        return {
            "stat_shift": {"power": 5, "speed": -5},
            "ability_boost": 10,
        }

    bot, bots = _make_evolve_bot(evolve_fn)
    bot.ability = AbilityDef(
        name="Zap", type="damage", potency=10,
        range=1, cooldown=2, energy_cost=10,
    )
    original_power = bot.stats.power
    events = run_evolve_callbacks(bots, round_num=5, grid_size=10, storm_border=0)
    assert bot.stats.power == original_power + 5
    assert bot.ability.potency == 20  # 10 + 10
    assert events[0]["stat_shift"] == {"power": 5, "speed": -5}
    assert events[0]["ability_boost"] == 10
