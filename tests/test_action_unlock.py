"""Tests for action unlock gating in engine/sandbox.py."""

from engine.sandbox import validate_action, BASE_ACTIONS, ACTION_UNLOCK_THRESHOLDS


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
