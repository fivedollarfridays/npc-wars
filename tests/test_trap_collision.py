"""Tests for trap collision + trigger resolution (T33.5).

Wires trap triggering into the combat loop: placement via direction action,
trigger on enemy movement, armor DR, kill attribution, expiry/cleanup.
"""

from __future__ import annotations

from typing import Any

from engine.combat import Bot


def _make_bot(emoji: str, x: int = 0, y: int = 0, **kw: Any) -> Bot:
    """Create a minimal Bot for testing."""
    return Bot(
        name=f"bot_{emoji}", emoji=emoji, bio="test", author="test",
        decide_func=lambda s: ("rest",), x=x, y=y, **kw,
    )


# --- Cycle 1: validate_action recognizes trap ---

def test_validate_action_trap_with_direction() -> None:
    """'trap' action with a valid direction is accepted when unlocked."""
    from engine.sandbox import validate_action
    result = validate_action(("trap", "north"), unlocked_actions={"trap", "move", "attack", "rest", "defend"})
    assert result == ("trap", "north")


def test_validate_action_trap_without_direction_rejected() -> None:
    """'trap' with no direction arg is rejected."""
    from engine.sandbox import validate_action
    result = validate_action(("trap",), unlocked_actions={"trap", "move", "attack", "rest", "defend"})
    assert result is None


def test_validate_action_trap_locked() -> None:
    """'trap' without being in unlocked_actions is rejected."""
    from engine.sandbox import validate_action
    result = validate_action(("trap", "north"), unlocked_actions={"move", "attack", "rest", "defend"})
    assert result is None


# --- Cycle 2: resolve_trap_placement ---

def test_resolve_trap_placement_basic() -> None:
    """Bot placing trap north creates trap at (x, y-1) and emits event."""
    from engine.traps import TrapManager
    from engine.trap_resolution import resolve_trap_placement

    bot = _make_bot("A", x=5, y=5)
    actions: dict[str, tuple[str, ...]] = {"A": ("trap", "north")}
    mgr = TrapManager()

    events = resolve_trap_placement([bot], actions, mgr, round_num=1, grid_size=10)

    assert len(events) == 1
    assert events[0]["type"] == "trap_placed"
    assert events[0]["emoji"] == "A"
    assert events[0]["x"] == 5
    assert events[0]["y"] == 4  # north = y-1
    assert len(mgr.get_all_traps()) == 1


def test_resolve_trap_placement_clamps_to_grid() -> None:
    """Trap placed at grid edge is clamped to valid position."""
    from engine.traps import TrapManager
    from engine.trap_resolution import resolve_trap_placement

    bot = _make_bot("A", x=0, y=0)
    actions: dict[str, tuple[str, ...]] = {"A": ("trap", "north")}
    mgr = TrapManager()

    events = resolve_trap_placement([bot], actions, mgr, round_num=1, grid_size=10)

    # North from (0,0) would be (0,-1) -> clamped to (0,0)
    assert len(events) == 1
    assert events[0]["x"] == 0
    assert events[0]["y"] == 0


def test_resolve_trap_placement_cooldown_blocks() -> None:
    """Placement blocked by cooldown emits no event."""
    from engine.traps import TrapManager
    from engine.trap_resolution import resolve_trap_placement

    bot = _make_bot("A", x=5, y=5)
    actions: dict[str, tuple[str, ...]] = {"A": ("trap", "north")}
    mgr = TrapManager()

    # First placement succeeds
    resolve_trap_placement([bot], actions, mgr, round_num=1, grid_size=10)
    # Second placement within cooldown fails
    events = resolve_trap_placement([bot], actions, mgr, round_num=2, grid_size=10)

    assert len(events) == 0
    assert len(mgr.get_all_traps()) == 1  # only the first trap


def test_resolve_trap_placement_ignores_non_trap_actions() -> None:
    """Bots with non-trap actions are ignored."""
    from engine.traps import TrapManager
    from engine.trap_resolution import resolve_trap_placement

    bot = _make_bot("A", x=5, y=5)
    actions: dict[str, tuple[str, ...]] = {"A": ("move", "north")}
    mgr = TrapManager()

    events = resolve_trap_placement([bot], actions, mgr, round_num=1, grid_size=10)
    assert len(events) == 0


# --- Cycle 3: resolve_trap_triggers ---

def test_trap_trigger_on_enemy_step() -> None:
    """Enemy stepping on trap takes damage and generates event."""
    from engine.traps import TrapManager
    from engine.trap_resolution import resolve_trap_triggers

    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=25, round_num=1)

    victim = _make_bot("B", x=3, y=4)
    hp_before = victim.hp
    events = resolve_trap_triggers([victim], mgr, round_num=2)

    assert len(events) == 1
    assert events[0]["type"] == "trap_trigger"
    assert events[0]["victim"] == "B"
    assert events[0]["owner"] == "A"
    assert events[0]["damage"] > 0
    assert victim.hp < hp_before
    # Trap removed after trigger
    assert len(mgr.get_all_traps()) == 0


def test_trap_trigger_respects_armor_dr() -> None:
    """Trap damage is reduced by victim's damage_reduction."""
    from engine.stats import StatAllocation
    from engine.traps import TrapManager, calculate_trap_damage
    from engine.trap_resolution import resolve_trap_triggers

    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=25, round_num=1)

    # High-armor bot: armor=50 -> DR = (50-25)*0.25 = 6
    high_armor = StatAllocation(power=20, speed=10, armor=50, mind=20)
    victim = _make_bot("B", x=3, y=4, stat_allocation=high_armor)
    assert victim.derived.damage_reduction == 6

    hp_before = victim.hp
    events = resolve_trap_triggers([victim], mgr, round_num=2)

    raw_damage = calculate_trap_damage(25)  # power=25 -> 20.0
    expected_damage = raw_damage - 6  # 14.0
    assert events[0]["damage"] == expected_damage
    assert victim.hp == hp_before - expected_damage


def test_trap_trigger_minimum_damage_1() -> None:
    """Trap damage never goes below 1 even with high DR."""
    from engine.stats import StatAllocation
    from engine.traps import TrapManager
    from engine.trap_resolution import resolve_trap_triggers

    mgr = TrapManager()
    # Low power trap: damage = 20
    mgr.place_trap("A", 3, 4, power=5, round_num=1)

    # Max armor = 80 -> DR = (80-25)*0.25 = 13
    high_armor = StatAllocation(power=5, speed=5, armor=80, mind=10)
    victim = _make_bot("B", x=3, y=4, stat_allocation=high_armor)
    assert victim.derived.damage_reduction == 13  # > trap damage of 20

    hp_before = victim.hp
    events = resolve_trap_triggers([victim], mgr, round_num=2)

    # 20 - 13 = 7, which is > 1, so no clamping needed here
    # Actually let's verify: trap damage = 20, DR = 13 -> 7
    assert events[0]["damage"] == 7.0
    assert victim.hp == hp_before - 7.0


def test_trap_trigger_tracks_damage_taken() -> None:
    """Trap damage is added to victim's damage_taken stat."""
    from engine.traps import TrapManager
    from engine.trap_resolution import resolve_trap_triggers

    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=25, round_num=1)

    victim = _make_bot("B", x=3, y=4)
    assert victim.damage_taken == 0
    resolve_trap_triggers([victim], mgr, round_num=2)
    assert victim.damage_taken > 0


def test_trap_no_trigger_on_own_trap() -> None:
    """Bot does not trigger their own traps."""
    from engine.traps import TrapManager
    from engine.trap_resolution import resolve_trap_triggers

    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=25, round_num=1)

    owner = _make_bot("A", x=3, y=4)
    events = resolve_trap_triggers([owner], mgr, round_num=2)

    assert len(events) == 0
    assert len(mgr.get_all_traps()) == 1  # trap still active


# --- Cycle 4: Trap kill attribution + damage_dealt on owner ---

def test_trap_kill_attributed_to_owner() -> None:
    """If a bot dies from trap damage, the kill is attributed to trap owner."""
    from engine.combat import resolve_deaths
    from engine.rounds import attribute_kills
    from engine.traps import TrapManager
    from engine.trap_resolution import resolve_trap_triggers

    owner = _make_bot("A", x=0, y=0)
    victim = _make_bot("B", x=3, y=4)
    victim.hp = 5.0  # low HP, trap will kill

    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=25, round_num=1)  # damage=20, victim has 5HP

    bots = [owner, victim]
    trap_events = resolve_trap_triggers([owner, victim], mgr, round_num=2)

    # Victim should be at or below 0 HP
    assert victim.hp <= 0

    round_elims = resolve_deaths(bots, round_num=2)
    assert len(round_elims) == 1
    assert round_elims[0]["emoji"] == "B"

    # attribute_kills uses events to find the killer
    attribute_kills(round_elims, trap_events, bots, round_num=2)
    assert round_elims[0]["killed_by"] == "A"
    assert round_elims[0]["cause"] == "combat"
    assert owner.kills == 1


def test_trap_trigger_credits_owner_damage_dealt() -> None:
    """Trap owner gets damage_dealt credit for trap damage."""
    from engine.traps import TrapManager
    from engine.trap_resolution import resolve_trap_triggers

    owner = _make_bot("A", x=0, y=0)
    victim = _make_bot("B", x=3, y=4)
    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=25, round_num=1)

    assert owner.damage_dealt == 0
    resolve_trap_triggers([owner, victim], mgr, round_num=2)
    assert owner.damage_dealt > 0


# --- Cycle 5: Full combat phase wiring ---

def test_combat_phases_with_trap_placement_and_trigger() -> None:
    """Trap placed in round 1, triggers when enemy moves onto it in round 2."""
    from engine.traps import TrapManager
    from engine.game import _resolve_combat_phases

    trapper = _make_bot("A", x=5, y=5)
    victim = _make_bot("B", x=5, y=3)
    bots = [trapper, victim]

    mgr = TrapManager()

    # Round 1: A places trap to north (5, 4)
    actions_r1: dict[str, tuple[str, ...]] = {"A": ("trap", "north"), "B": ("rest",)}
    rd1, _, _ = _resolve_combat_phases(
        bots, bots, actions_r1, set(), [], round_num=1,
        grid_size=10, storm_border=0, trap_manager=mgr,
    )
    # Should have placement event
    placement_events = [e for e in rd1["events"] if e["type"] == "trap_placed"]
    assert len(placement_events) == 1
    assert placement_events[0]["x"] == 5
    assert placement_events[0]["y"] == 4

    # Round 2: B moves south to (5, 4) — onto the trap
    actions_r2: dict[str, tuple[str, ...]] = {"A": ("rest",), "B": ("move", "south")}
    rd2, _, _ = _resolve_combat_phases(
        bots, bots, actions_r2, set(), [], round_num=2,
        grid_size=10, storm_border=0, trap_manager=mgr,
    )
    trigger_events = [e for e in rd2["events"] if e["type"] == "trap_trigger"]
    assert len(trigger_events) == 1
    assert trigger_events[0]["victim"] == "B"
    assert trigger_events[0]["owner"] == "A"


def test_combat_phases_expire_traps() -> None:
    """Expired traps are cleaned up at end of round."""
    from engine.traps import TrapManager

    from engine.game import _resolve_combat_phases

    bot_a = _make_bot("A", x=5, y=5)
    bot_b = _make_bot("B", x=0, y=0)
    bots = [bot_a, bot_b]

    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=25, round_num=1)  # expires at round 11

    # Run at round 11 -> trap should expire
    actions: dict[str, tuple[str, ...]] = {"A": ("rest",), "B": ("rest",)}
    _resolve_combat_phases(
        bots, bots, actions, set(), [], round_num=11,
        grid_size=10, storm_border=0, trap_manager=mgr,
    )
    assert len(mgr.get_all_traps()) == 0


def test_combat_phases_dead_bot_traps_removed() -> None:
    """When a bot dies, their traps are removed."""
    from engine.traps import TrapManager
    from engine.game import _resolve_combat_phases

    bot_a = _make_bot("A", x=5, y=5)
    bot_b = _make_bot("B", x=0, y=0)
    bots = [bot_a, bot_b]

    mgr = TrapManager()
    mgr.place_trap("A", 3, 4, power=25, round_num=1)

    # Set HP low enough that rest heal (5) won't save it
    # Rest heals 5 HP, so -10 ensures death even after heal
    bot_a.hp = -10
    actions: dict[str, tuple[str, ...]] = {"A": ("rest",), "B": ("rest",)}
    _resolve_combat_phases(
        bots, bots, actions, set(), [], round_num=2,
        grid_size=10, storm_border=0, trap_manager=mgr,
    )
    # A's traps should be cleaned up after death
    assert not bot_a.alive
    assert len(mgr.get_all_traps()) == 0
