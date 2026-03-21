"""Tests for engine/traps.py — trap action system."""

from __future__ import annotations


# --- Cycle 1: calculate_trap_damage ---

def test_trap_damage_at_baseline_power() -> None:
    """Power == 25 (baseline) => base damage only, no scaling bonus."""
    from engine.traps import calculate_trap_damage
    assert calculate_trap_damage(25) == 20.0


def test_trap_damage_below_baseline() -> None:
    """Power < 25 => no bonus (clamped to 0)."""
    from engine.traps import calculate_trap_damage
    assert calculate_trap_damage(10) == 20.0


def test_trap_damage_above_baseline() -> None:
    """Power 35 => 20 + 0.5 * (35-25) = 25."""
    from engine.traps import calculate_trap_damage
    assert calculate_trap_damage(35) == 25.0


def test_trap_damage_zero_power() -> None:
    """Power 0 => still base damage only."""
    from engine.traps import calculate_trap_damage
    assert calculate_trap_damage(0) == 20.0


# --- Cycle 2: Trap dataclass ---

def test_trap_dataclass_creation() -> None:
    """Trap dataclass stores all required fields."""
    from engine.traps import Trap
    t = Trap(owner_emoji="A", x=3, y=4, damage=25.0, placed_round=5, expires_round=15)
    assert t.owner_emoji == "A"
    assert t.x == 3
    assert t.y == 4
    assert t.damage == 25.0
    assert t.placed_round == 5
    assert t.expires_round == 15


def test_trap_is_frozen() -> None:
    """Trap dataclass is immutable."""
    import dataclasses
    from engine.traps import Trap
    t = Trap(owner_emoji="A", x=0, y=0, damage=20.0, placed_round=1, expires_round=11)
    assert dataclasses.is_dataclass(t)
    try:
        t.x = 5  # type: ignore[misc]
        raise AssertionError("Should have raised FrozenInstanceError")
    except dataclasses.FrozenInstanceError:
        pass


# --- Cycle 3: TrapManager place + cooldown ---

def test_place_trap_success() -> None:
    """First placement should succeed."""
    from engine.traps import TrapManager
    mgr = TrapManager()
    trap = mgr.place_trap("A", 3, 4, power=30, round_num=1)
    assert trap is not None
    assert trap.owner_emoji == "A"
    assert trap.x == 3
    assert trap.y == 4
    assert trap.expires_round == 11  # placed_round(1) + TRAP_LIFETIME(10)


def test_place_trap_cooldown_blocks() -> None:
    """Placing a trap within cooldown window returns None."""
    from engine.traps import TrapManager
    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=25, round_num=1)
    # Rounds 2, 3 should be blocked (cooldown=3, so next allowed at round 4)
    assert mgr.place_trap("A", 5, 5, power=25, round_num=2) is None
    assert mgr.place_trap("A", 5, 5, power=25, round_num=3) is None


def test_place_trap_cooldown_expires() -> None:
    """After cooldown expires, can place again."""
    from engine.traps import TrapManager
    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=25, round_num=1)
    # Cooldown = 3, so round 1+3 = 4 is the next allowed round
    trap2 = mgr.place_trap("A", 5, 5, power=25, round_num=4)
    assert trap2 is not None


def test_get_cooldown_remaining() -> None:
    """get_cooldown returns remaining rounds."""
    from engine.traps import TrapManager
    mgr = TrapManager()
    assert mgr.get_cooldown_at("A", 1) == 0  # no trap placed yet
    mgr.place_trap("A", 0, 0, power=25, round_num=5)
    # Next allowed at round 8, so at round 6 => 2 rounds left
    assert mgr.get_cooldown_at("A", 6) == 2
    assert mgr.get_cooldown_at("A", 7) == 1
    assert mgr.get_cooldown_at("A", 8) == 0


def test_get_traps_for_owner() -> None:
    """get_traps_for returns only that owner's traps."""
    from engine.traps import TrapManager
    mgr = TrapManager()
    mgr.place_trap("A", 0, 0, power=25, round_num=1)
    mgr.place_trap("B", 1, 1, power=25, round_num=1)
    a_traps = mgr.get_traps_for("A")
    assert len(a_traps) == 1
    assert a_traps[0].owner_emoji == "A"


# --- Cycle 4: triggers, expiry, cleanup ---

def test_check_triggers_enemy_trap() -> None:
    """Stepping on enemy trap triggers it."""
    from engine.traps import TrapManager
    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=30, round_num=1)
    triggered = mgr.check_triggers("B", 3, 4, round_num=2)
    assert len(triggered) == 1
    assert triggered[0].owner_emoji == "A"
    # Trap should be removed after trigger
    assert len(mgr.get_traps_for("A")) == 0


def test_check_triggers_own_trap_no_trigger() -> None:
    """Stepping on own trap does not trigger it."""
    from engine.traps import TrapManager
    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=25, round_num=1)
    triggered = mgr.check_triggers("A", 3, 4, round_num=2)
    assert len(triggered) == 0
    # Trap should still exist
    assert len(mgr.get_traps_for("A")) == 1


def test_check_triggers_wrong_position() -> None:
    """No trigger if victim is at a different position."""
    from engine.traps import TrapManager
    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=25, round_num=1)
    triggered = mgr.check_triggers("B", 5, 5, round_num=2)
    assert len(triggered) == 0


def test_expire_traps() -> None:
    """Traps past their lifetime are expired."""
    from engine.traps import TrapManager
    mgr = TrapManager()
    mgr.place_trap("A", 0, 0, power=25, round_num=1)  # expires at round 11
    expired = mgr.expire_traps(round_num=11)
    assert len(expired) == 1
    assert expired[0].owner_emoji == "A"
    assert len(mgr.get_all_traps()) == 0


def test_expire_traps_not_yet() -> None:
    """Traps within lifetime are not expired."""
    from engine.traps import TrapManager
    mgr = TrapManager()
    mgr.place_trap("A", 0, 0, power=25, round_num=1)  # expires at round 11
    expired = mgr.expire_traps(round_num=10)
    assert len(expired) == 0
    assert len(mgr.get_all_traps()) == 1


def test_remove_bot_traps() -> None:
    """Dead bot cleanup removes all their traps."""
    from engine.traps import TrapManager
    mgr = TrapManager()
    mgr.place_trap("A", 0, 0, power=25, round_num=1)
    mgr.place_trap("A", 1, 1, power=25, round_num=4)  # after cooldown
    removed = mgr.remove_bot_traps("A")
    assert len(removed) == 2
    assert len(mgr.get_all_traps()) == 0


def test_get_all_traps() -> None:
    """get_all_traps returns traps from all owners."""
    from engine.traps import TrapManager
    mgr = TrapManager()
    mgr.place_trap("A", 0, 0, power=25, round_num=1)
    mgr.place_trap("B", 1, 1, power=25, round_num=1)
    assert len(mgr.get_all_traps()) == 2


# --- Cycle 5: ACTION_COSTS + Bot.trap_cooldown ---

def test_action_costs_includes_trap() -> None:
    """ACTION_COSTS dict has 'trap' with cost 15."""
    from engine.combat import ACTION_COSTS
    assert "trap" in ACTION_COSTS
    assert ACTION_COSTS["trap"] == 15


def test_bot_has_trap_cooldown_field() -> None:
    """Bot class has trap_cooldown field defaulting to 0."""
    from engine.combat import Bot
    bot = Bot(
        name="test", emoji="T", bio="test", author="test",
        decide_func=lambda *a, **kw: {"action": "rest"},
        x=0, y=0,
    )
    assert bot.trap_cooldown == 0
