"""Tests for malfunction events and bot unlocked_actions safety."""

from bots import example_trapper, viper
from engine.combat import MAX_CONSECUTIVE_FAILURES
from engine.rounds import resolve_decisions
from tests.conftest import make_bot


# ---------------------------------------------------------------------------
# Cycle 1: Malfunction event on 3 consecutive failures
# ---------------------------------------------------------------------------

def _crashing_decide(state):
    """Bot that always crashes."""
    raise RuntimeError("I'm broken")


def test_malfunction_event_generated_on_max_failures():
    """When a bot reaches MAX_CONSECUTIVE_FAILURES, a malfunction event is emitted."""
    bot = make_bot(
        name="Crasher", emoji="X", hp=100, energy=100, x=3, y=3,
        decide_func=_crashing_decide,
        consecutive_failures=MAX_CONSECUTIVE_FAILURES - 1,
    )
    other = make_bot(name="Other", emoji="O", hp=100, energy=100, x=7, y=7)
    alive = [bot, other]
    all_bots = [bot, other]

    actions, _, override_events = resolve_decisions(
        alive, all_bots, round_num=5, grid_size=10, storm_border=0,
    )

    # Bot should be dead
    assert bot.hp == 0
    assert actions["X"] == ("disconnected",)

    # Malfunction event should exist in override_events
    malfunctions = [e for e in override_events if e["type"] == "malfunction"]
    assert len(malfunctions) == 1


def test_malfunction_event_has_required_fields():
    """Malfunction event must contain type, emoji, reason, and round."""
    bot = make_bot(
        name="Crasher", emoji="X", hp=100, energy=100, x=3, y=3,
        decide_func=_crashing_decide,
        consecutive_failures=MAX_CONSECUTIVE_FAILURES - 1,
    )
    other = make_bot(name="Other", emoji="O", hp=100, energy=100, x=7, y=7)

    _, _, override_events = resolve_decisions(
        [bot, other], [bot, other], round_num=7, grid_size=10, storm_border=0,
    )

    evt = [e for e in override_events if e["type"] == "malfunction"][0]
    assert evt["emoji"] == "X"
    assert "reason" in evt
    assert evt["round"] == 7


def test_bot_is_dead_after_malfunction():
    """Bot with malfunction should have hp == 0 (check_eliminations sets alive=False later)."""
    bot = make_bot(
        name="Crasher", emoji="X", hp=100, energy=100, x=3, y=3,
        decide_func=_crashing_decide,
        consecutive_failures=MAX_CONSECUTIVE_FAILURES - 1,
    )
    other = make_bot(name="Other", emoji="O", hp=100, energy=100, x=7, y=7)

    actions, _, _ = resolve_decisions(
        [bot, other], [bot, other], round_num=1, grid_size=10, storm_border=0,
    )

    assert bot.hp == 0
    assert actions["X"] == ("disconnected",)


# ---------------------------------------------------------------------------
# Cycle 2: Trapper bot handles missing trap unlock
# ---------------------------------------------------------------------------

def test_trapper_valid_action_without_trap_unlocked():
    """Trapper should return a valid action even without 'trap' unlocked."""
    state = {
        "me": {
            "x": 5, "y": 5, "hp": 100, "energy": 50,
            "trap_cooldown": 0,
            "unlocked_actions": ["move", "attack", "rest", "defend"],
        },
        "enemies": [{"emoji": "E", "x": 5, "y": 3, "hp": 80}],
        "grid_size": 10,
        "round": 5,
        "storm_border": 0,
    }
    action = example_trapper.decide(state)
    assert action[0] != "trap", f"Trapper returned trap without it being unlocked: {action}"
    assert action[0] in ("move", "attack", "rest", "defend")


def test_trapper_can_trap_when_unlocked():
    """Trapper should still use trap when it IS unlocked."""
    state = {
        "me": {
            "x": 5, "y": 5, "hp": 100, "energy": 50,
            "trap_cooldown": 0,
            "unlocked_actions": ["move", "attack", "rest", "defend", "trap"],
        },
        "enemies": [{"emoji": "E", "x": 5, "y": 3, "hp": 80}],
        "grid_size": 10,
        "round": 5,
        "storm_border": 0,
    }
    action = example_trapper.decide(state)
    # Should be able to trap (enemy is at dist=2, energy >= 15, cooldown=0)
    assert action[0] == "trap"


# ---------------------------------------------------------------------------
# Cycle 3: Viper bot handles missing trap unlock
# ---------------------------------------------------------------------------

def test_viper_valid_action_without_trap_unlocked():
    """Viper should return a valid action even without 'trap' unlocked."""
    # Reset viper's module state
    viper._tracked.clear()
    viper._last_positions.clear()
    viper._trap_tiles.clear()

    state = {
        "me": {
            "x": 5, "y": 5, "hp": 100, "energy": 50, "max_hp": 145,
            "trap_cooldown": 0, "min_damage": 22,
            "hit_chance_vs": {},
            "is_leader": False,
            "unlocked_actions": ["move", "attack", "rest", "defend"],
        },
        "enemies": [{"emoji": "E", "x": 5, "y": 2, "hp": 80, "is_leader": False}],
        "grid_size": 10,
        "round": 10,
        "storm_border": 0,
    }
    action = viper.decide(state)
    assert action[0] != "trap", f"Viper returned trap without it being unlocked: {action}"
    assert action[0] in ("move", "attack", "rest", "defend")


def test_viper_can_trap_when_unlocked():
    """Viper should still use trap when it IS unlocked."""
    viper._tracked.clear()
    viper._last_positions.clear()
    viper._trap_tiles.clear()

    state = {
        "me": {
            "x": 5, "y": 5, "hp": 100, "energy": 50, "max_hp": 145,
            "trap_cooldown": 0, "min_damage": 22,
            "hit_chance_vs": {},
            "is_leader": False,
            "unlocked_actions": ["move", "attack", "rest", "defend", "trap"],
        },
        "enemies": [{"emoji": "E", "x": 5, "y": 2, "hp": 80, "is_leader": False}],
        "grid_size": 10,
        "round": 10,
        "storm_border": 0,
    }
    action = viper.decide(state)
    # Viper at (5,5), enemy at (5,2) = dist 3, trap_cd=0, energy>=25 -> should trap
    assert action[0] == "trap"
