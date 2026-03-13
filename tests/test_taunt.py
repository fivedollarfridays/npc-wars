"""Tests for taunt action mechanics."""

from tests.conftest import make_bot
from engine.sandbox import validate_action, VALID_ACTIONS
from engine.combat import ACTION_COSTS, TAUNT_COST, TAUNT_RANGE
from engine.grid import direction_toward
from engine.rounds import resolve_taunt, _apply_taunt_override


# --- Cycle 1: Constants and validation ---


def test_taunt_cost_is_10():
    assert TAUNT_COST == 10


def test_taunt_range_is_2():
    assert TAUNT_RANGE == 2


def test_taunt_in_action_costs():
    assert ACTION_COSTS["taunt"] == TAUNT_COST


def test_validate_taunt_action():
    """("taunt",) is a valid action with 0 args."""
    result = validate_action(("taunt",))
    assert result == ("taunt",)


def test_taunt_in_valid_actions():
    assert "taunt" in VALID_ACTIONS
    assert VALID_ACTIONS["taunt"] == 0


# --- Cycle 2: resolve_taunt ---


def test_bot_has_taunt_target_attr():
    bot = make_bot()
    assert bot.taunt_target is None


def test_resolve_taunt_sets_target_on_nearby_bot():
    """Bot within Manhattan distance 2 gets taunt_target set."""
    taunter = make_bot(emoji="T", x=5, y=5)
    victim = make_bot(emoji="V", x=6, y=5)  # distance 1
    actions = {"T": ("taunt",), "V": ("rest",)}
    events = resolve_taunt([taunter, victim], actions)
    assert victim.taunt_target == "T"
    assert len(events) == 1
    assert events[0]["type"] == "taunt"
    assert events[0]["taunter"] == "T"
    assert "V" in events[0]["affected"]


def test_resolve_taunt_ignores_distant_bot():
    """Bot beyond Manhattan distance 2 is NOT affected."""
    taunter = make_bot(emoji="T", x=5, y=5)
    far_bot = make_bot(emoji="F", x=8, y=5)  # distance 3
    actions = {"T": ("taunt",), "F": ("rest",)}
    resolve_taunt([taunter, far_bot], actions)
    assert far_bot.taunt_target is None


def test_resolve_taunt_event_structure():
    """Taunt event has type, taunter, and affected list."""
    taunter = make_bot(emoji="T", x=5, y=5)
    v1 = make_bot(emoji="A", x=5, y=6)  # distance 1
    v2 = make_bot(emoji="B", x=6, y=6)  # distance 2
    actions = {"T": ("taunt",), "A": ("rest",), "B": ("rest",)}
    events = resolve_taunt([taunter, v1, v2], actions)
    assert len(events) == 1
    evt = events[0]
    assert evt["type"] == "taunt"
    assert evt["taunter"] == "T"
    assert set(evt["affected"]) == {"A", "B"}


def test_resolve_taunt_does_not_affect_taunter():
    """Taunter should not taunt themselves."""
    taunter = make_bot(emoji="T", x=5, y=5)
    actions = {"T": ("taunt",)}
    events = resolve_taunt([taunter], actions)
    assert taunter.taunt_target is None
    # No one affected, so no event (or empty affected list)
    if events:
        assert "T" not in events[0]["affected"]


# --- Cycle 3: direction_toward and taunt override ---


def testdirection_toward_east():
    assert direction_toward(0, 0, 3, 0) == "east"


def testdirection_toward_west():
    assert direction_toward(5, 5, 2, 5) == "west"


def testdirection_toward_south():
    assert direction_toward(5, 5, 5, 8) == "south"


def testdirection_toward_north():
    assert direction_toward(5, 5, 5, 2) == "north"


def testdirection_toward_tie_breaks_x():
    """When dx == dy, prefer x-axis (east/west)."""
    assert direction_toward(0, 0, 2, 2) == "east"
    assert direction_toward(5, 5, 3, 3) == "west"


def test_taunted_bot_attack_redirected():
    """A taunted bot's attack gets redirected toward the taunter."""
    taunter = make_bot(emoji="T", x=5, y=5, alive=True)
    victim = make_bot(emoji="V", x=7, y=5)
    victim.taunt_target = "T"
    # Victim chose attack east, but taunter is west
    result = _apply_taunt_override(victim, ("attack", "east"), [taunter, victim])
    assert result == ("attack", "west")


def test_taunt_target_cleared_after_consumption():
    """After taunt override is consumed, taunt_target should be None."""
    taunter = make_bot(emoji="T", x=5, y=5, alive=True)
    victim = make_bot(emoji="V", x=6, y=5)
    victim.taunt_target = "T"
    _apply_taunt_override(victim, ("attack", "east"), [taunter, victim])
    assert victim.taunt_target is None


def test_taunt_override_dead_taunter_keeps_original():
    """If taunter is dead, keep original attack direction and clear taunt_target."""
    taunter = make_bot(emoji="T", x=5, y=5, alive=False)
    victim = make_bot(emoji="V", x=6, y=5)
    victim.taunt_target = "T"
    result = _apply_taunt_override(victim, ("attack", "east"), [taunter, victim])
    assert result == ("attack", "east")
    assert victim.taunt_target is None
