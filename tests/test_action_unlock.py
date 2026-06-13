"""Tests for action unlock gating in engine/sandbox.py."""

from engine.sandbox import (
    ACTION_UNLOCK_THRESHOLDS,
    BASE_ACTIONS,
    LOCKED,
    classify_action,
    validate_action,
)


class TestConstants:
    def test_base_actions_contains_exactly_four(self):
        assert BASE_ACTIONS == frozenset({"move", "attack", "rest", "defend"})

    def test_action_unlock_thresholds(self):
        assert ACTION_UNLOCK_THRESHOLDS == {
            "ranged_attack": 3,
            "dash": 5,
            "taunt": 10,
        }


class TestBaseActionsAlwaysAllowed:
    """Base 4 actions pass validation even when unlocked_actions is an empty set."""

    def test_move_with_empty_unlocked(self):
        assert validate_action(("move", "north"), unlocked_actions=set()) == ("move", "north")

    def test_attack_with_empty_unlocked(self):
        assert validate_action(("attack", "south"), unlocked_actions=set()) == ("attack", "south")

    def test_rest_with_empty_unlocked(self):
        assert validate_action(("rest",), unlocked_actions=set()) == ("rest",)

    def test_defend_with_empty_unlocked(self):
        assert validate_action(("defend",), unlocked_actions=set()) == ("defend",)


class TestLockedActionsRejected:
    """Non-base actions rejected when not in unlocked_actions."""

    def test_ranged_attack_rejected_when_locked(self):
        result = validate_action(("ranged_attack", "north"), unlocked_actions=set())
        assert result is None

    def test_dash_rejected_when_locked(self):
        result = validate_action(("dash", "east"), unlocked_actions=set())
        assert result is None

    def test_taunt_rejected_when_locked(self):
        result = validate_action(("taunt",), unlocked_actions=set())
        assert result is None


class TestUnlockedActionsAccepted:
    """Non-base actions accepted when present in unlocked_actions."""

    def test_ranged_attack_accepted_when_unlocked(self):
        result = validate_action(("ranged_attack", "west"), unlocked_actions={"ranged_attack"})
        assert result == ("ranged_attack", "west")

    def test_dash_accepted_when_unlocked(self):
        result = validate_action(("dash", "south"), unlocked_actions={"dash"})
        assert result == ("dash", "south")

    def test_taunt_accepted_when_unlocked(self):
        result = validate_action(("taunt",), unlocked_actions={"taunt"})
        assert result == ("taunt",)


class TestBackwardCompatibility:
    """When unlocked_actions is None (default), all valid actions pass."""

    def test_ranged_attack_passes_without_unlock_param(self):
        assert validate_action(("ranged_attack", "north")) == ("ranged_attack", "north")

    def test_dash_passes_without_unlock_param(self):
        assert validate_action(("dash", "east")) == ("dash", "east")

    def test_taunt_passes_without_unlock_param(self):
        assert validate_action(("taunt",)) == ("taunt",)


class TestLockedActionDegradesInResolveDecisions:
    """A locked-but-well-formed action degrades to rest without penalty."""

    def _setup(self, locked_action):
        from tests.conftest import make_bot
        from engine.rounds_decisions import resolve_decisions

        bot = make_bot(name="Locked", emoji="L", hp=80, energy=100, x=2, y=2,
                       decide_func=lambda s: locked_action)
        bot.unlocked_actions = ["move", "attack", "rest", "defend"]
        return bot, resolve_decisions

    def test_locked_trap_degrades_to_rest(self):
        bot, resolve_decisions = self._setup(("trap", "north"))
        actions, _forced, _events = resolve_decisions(
            [bot], [bot], round_num=1, grid_size=12, storm_border=0,
        )
        assert actions[bot.emoji] == ("rest",)

    def test_locked_action_does_not_increment_failures(self):
        bot, resolve_decisions = self._setup(("trap", "north"))
        resolve_decisions([bot], [bot], round_num=1, grid_size=12, storm_border=0)
        assert bot.consecutive_failures == 0

    def test_locked_action_emits_locked_action_event(self):
        bot, resolve_decisions = self._setup(("use_ability",))
        _actions, _forced, events = resolve_decisions(
            [bot], [bot], round_num=1, grid_size=12, storm_border=0,
        )
        locked_events = [e for e in events if e.get("type") == "locked_action"]
        assert len(locked_events) == 1
        ev = locked_events[0]
        assert ev["player"] == bot.emoji
        assert ev["action"] == "use_ability"

    def test_repeated_locked_never_disconnects(self):
        bot, resolve_decisions = self._setup(("trap", "north"))
        for r in range(1, 6):
            actions, _forced, _events = resolve_decisions(
                [bot], [bot], round_num=r, grid_size=12, storm_border=0,
            )
            assert actions[bot.emoji] == ("rest",)
        assert bot.consecutive_failures == 0
        assert bot.hp == 80

    def test_malformed_still_increments_failures(self):
        bot, resolve_decisions = self._setup(("fly", "north"))
        resolve_decisions([bot], [bot], round_num=1, grid_size=12, storm_border=0)
        assert bot.consecutive_failures == 1


class TestClassifyLockedVsMalformed:
    """classify_action separates well-formed-but-locked from malformed."""

    def test_locked_trap_is_locked(self):
        assert classify_action(("trap", "north"), set()) is LOCKED

    def test_locked_use_ability_is_locked(self):
        assert classify_action(("use_ability",), set()) is LOCKED

    def test_unlocked_trap_returns_normalized(self):
        assert classify_action(("trap", "south"), {"trap"}) == ("trap", "south")

    def test_malformed_is_none_not_locked(self):
        assert classify_action(("fly", "north"), set()) is None

    def test_base_action_never_locked(self):
        assert classify_action(("move", "north"), set()) == ("move", "north")
