"""Tests for human_override events emitted during copilot overrides."""

from engine.human_input import MockInputAdapter
from engine.rounds import resolve_decisions
from tests.conftest import make_bot


# ---------------------------------------------------------------------------
# Cycle 1: Override generates event with correct fields
# ---------------------------------------------------------------------------

def test_human_override_emits_event():
    """When human overrides with a different action, a human_override event is emitted."""
    adapter = MockInputAdapter([("attack", "north")])
    bot = make_bot(name="Copilot", emoji="C", x=3, y=3)
    bot.human_adapter = adapter
    # Bot's default decide_func returns ("rest",)

    actions, forced_rest, override_events = resolve_decisions(
        alive_bots=[bot], bots=[bot], round_num=1,
        grid_size=10, storm_border=0,
    )

    assert len(override_events) == 1
    evt = override_events[0]
    assert evt["type"] == "human_override"
    assert evt["player"] == "C"
    assert evt["original"] == "rest"
    assert evt["override"] == "attack north"


def test_human_override_event_action_strings_are_readable():
    """Event action strings use space-separated human-readable format."""
    adapter = MockInputAdapter([("move", "south")])
    bot = make_bot(name="Copilot", emoji="C", x=3, y=3)
    bot.human_adapter = adapter

    _, _, override_events = resolve_decisions(
        alive_bots=[bot], bots=[bot], round_num=1,
        grid_size=10, storm_border=0,
    )

    evt = override_events[0]
    assert evt["original"] == "rest"
    assert evt["override"] == "move south"


# ---------------------------------------------------------------------------
# Cycle 2: No event when human returns None or same action
# ---------------------------------------------------------------------------

def test_no_event_when_human_returns_none():
    """No override event when human adapter times out (returns None)."""
    adapter = MockInputAdapter([None])
    bot = make_bot(name="Copilot", emoji="C", x=3, y=3)
    bot.human_adapter = adapter

    _, _, override_events = resolve_decisions(
        alive_bots=[bot], bots=[bot], round_num=1,
        grid_size=10, storm_border=0,
    )

    assert override_events == []


def test_no_event_when_human_matches_bot():
    """No override event when human action matches the bot's original action."""
    # Bot's default decide_func returns ("rest",), human also picks ("rest",)
    adapter = MockInputAdapter([("rest",)])
    bot = make_bot(name="Copilot", emoji="C", x=3, y=3)
    bot.human_adapter = adapter

    _, _, override_events = resolve_decisions(
        alive_bots=[bot], bots=[bot], round_num=1,
        grid_size=10, storm_border=0,
    )

    assert override_events == []


# ---------------------------------------------------------------------------
# Cycle 3: Multiple humans overriding each get their own event
# ---------------------------------------------------------------------------

def test_multiple_humans_each_get_own_event():
    """Each human that overrides their bot generates a separate event."""
    adapter_a = MockInputAdapter([("attack", "north")])
    adapter_b = MockInputAdapter([("move", "east")])
    bot_a = make_bot(name="HumanA", emoji="A", x=1, y=1)
    bot_a.human_adapter = adapter_a
    bot_b = make_bot(name="HumanB", emoji="B", x=8, y=8)
    bot_b.human_adapter = adapter_b

    _, _, override_events = resolve_decisions(
        alive_bots=[bot_a, bot_b], bots=[bot_a, bot_b],
        round_num=1, grid_size=10, storm_border=0,
    )

    assert len(override_events) == 2
    players = {e["player"] for e in override_events}
    assert players == {"A", "B"}
