"""Tests for copilot override logic in the round resolution pipeline."""

from engine.human_input import MockInputAdapter
from engine.rounds import resolve_decisions
from tests.conftest import make_bot


# ---------------------------------------------------------------------------
# Cycle 1: Human override replaces bot's decide() output
# ---------------------------------------------------------------------------

def test_human_override_replaces_bot_decision():
    """When a human adapter returns a valid action, it replaces the bot's decide()."""
    adapter = MockInputAdapter([("attack", "north")])
    bot = make_bot(name="Copilot", emoji="C", x=3, y=3)
    bot.human_adapter = adapter
    # Bot's decide_func always returns ("rest",) by default from make_bot

    actions, _, _ = resolve_decisions(
        alive_bots=[bot], bots=[bot], round_num=1,
        grid_size=10, storm_border=0,
    )

    assert actions["C"] == ("attack", "north")


def test_human_override_does_not_affect_other_bots():
    """Only the bot with a human adapter gets overridden; others keep their own decision."""
    adapter = MockInputAdapter([("attack", "east")])
    human_bot = make_bot(name="Human", emoji="H", x=1, y=1)
    human_bot.human_adapter = adapter

    ai_bot = make_bot(name="AI", emoji="A", x=8, y=8)
    # ai_bot has no human_adapter

    actions, _, _ = resolve_decisions(
        alive_bots=[human_bot, ai_bot], bots=[human_bot, ai_bot],
        round_num=1, grid_size=10, storm_border=0,
    )

    assert actions["H"] == ("attack", "east")
    assert actions["A"] == ("rest",)  # default decide_func from make_bot


# ---------------------------------------------------------------------------
# Cycle 2: No human override (adapter returns None) uses bot's original
# ---------------------------------------------------------------------------

def test_no_human_override_uses_bot_decision():
    """When the human adapter returns None (timeout), bot's decide() is used."""
    adapter = MockInputAdapter([None])  # simulates timeout
    bot = make_bot(name="Copilot", emoji="C", x=3, y=3)
    bot.human_adapter = adapter

    actions, _, _ = resolve_decisions(
        alive_bots=[bot], bots=[bot], round_num=1,
        grid_size=10, storm_border=0,
    )

    # Bot's default decide_func returns ("rest",)
    assert actions["C"] == ("rest",)


def test_no_adapter_attached_uses_bot_decision():
    """Bot without human_adapter uses its own decide() output normally."""
    bot = make_bot(name="Solo", emoji="S", x=3, y=3)
    # No adapter attached (human_adapter defaults to None)

    actions, _, _ = resolve_decisions(
        alive_bots=[bot], bots=[bot], round_num=1,
        grid_size=10, storm_border=0,
    )

    assert actions["S"] == ("rest",)


# ---------------------------------------------------------------------------
# Cycle 3: Human sees the same state dict the bot receives
# ---------------------------------------------------------------------------

class StateCapturingAdapter(MockInputAdapter):
    """Adapter that captures the state dict passed to get_action."""

    def __init__(self, actions):
        super().__init__(actions)
        self.captured_states: list[dict] = []

    def get_action(self, state, timeout_s):
        self.captured_states.append(state)
        return super().get_action(state, timeout_s)


def test_human_receives_same_state_as_bot():
    """The human adapter receives the identical state dict built for the bot."""
    adapter = StateCapturingAdapter([("rest",)])
    bot = make_bot(name="Copilot", emoji="C", x=3, y=3)
    bot.human_adapter = adapter

    resolve_decisions(
        alive_bots=[bot], bots=[bot], round_num=5,
        grid_size=10, storm_border=1,
    )

    assert len(adapter.captured_states) == 1
    state = adapter.captured_states[0]
    # Verify the state contains the bot's own info
    assert state["round"] == 5
    assert state["me"]["x"] == 3
    assert state["me"]["y"] == 3


# ---------------------------------------------------------------------------
# Cycle 4: Invalid human action validated and rejected, bot fallback
# ---------------------------------------------------------------------------

def test_invalid_human_action_falls_back_to_bot():
    """If the human provides an invalid action, the bot's decide() result is used."""
    # "fly" is not a valid action
    adapter = MockInputAdapter([("fly", "up")])
    bot = make_bot(name="Copilot", emoji="C", x=3, y=3)
    bot.human_adapter = adapter

    actions, _, _ = resolve_decisions(
        alive_bots=[bot], bots=[bot], round_num=1,
        grid_size=10, storm_border=0,
    )

    # Bot's default decide_func returns ("rest",)
    assert actions["C"] == ("rest",)


def test_invalid_direction_human_action_falls_back():
    """Human action with invalid direction (e.g. 'move diagonal') falls back to bot."""
    adapter = MockInputAdapter([("move", "diagonal")])
    bot = make_bot(name="Copilot", emoji="C", x=3, y=3)
    bot.human_adapter = adapter

    actions, _, _ = resolve_decisions(
        alive_bots=[bot], bots=[bot], round_num=1,
        grid_size=10, storm_border=0,
    )

    assert actions["C"] == ("rest",)


# ---------------------------------------------------------------------------
# Cycle 5: Locked action override falls back to bot
# ---------------------------------------------------------------------------

def test_locked_human_action_falls_back_to_bot():
    """Human tries 'dash' but bot hasn't unlocked it; falls back to bot decide."""
    adapter = MockInputAdapter([("dash", "north")])
    bot = make_bot(name="Copilot", emoji="C", x=3, y=3)
    bot.human_adapter = adapter
    # Default unlocked_actions = ["attack", "defend", "move", "rest"] -- no "dash"

    actions, _, _ = resolve_decisions(
        alive_bots=[bot], bots=[bot], round_num=1,
        grid_size=10, storm_border=0,
    )

    assert actions["C"] == ("rest",)


def test_unlocked_action_human_override_accepted():
    """Human tries 'dash' and bot has it unlocked; override is accepted."""
    adapter = MockInputAdapter([("dash", "north")])
    bot = make_bot(name="Copilot", emoji="C", x=3, y=3)
    bot.human_adapter = adapter
    bot.unlocked_actions = sorted({"move", "attack", "rest", "defend", "dash"})

    actions, _, _ = resolve_decisions(
        alive_bots=[bot], bots=[bot], round_num=1,
        grid_size=10, storm_border=0,
    )

    assert actions["C"] == ("dash", "north")
