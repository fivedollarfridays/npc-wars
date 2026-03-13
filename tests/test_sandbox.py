"""Tests for engine/sandbox.py — action validation, bot execution, timeout."""

import time

from engine.sandbox import execute_decide, validate_action


# --- validate_action ---


class TestValidateAction:
    def test_valid_move(self):
        assert validate_action(("move", "north")) == ("move", "north")

    def test_valid_attack(self):
        assert validate_action(("attack", "south")) == ("attack", "south")

    def test_valid_rest(self):
        assert validate_action(("rest",)) == ("rest",)

    def test_valid_defend(self):
        assert validate_action(("defend",)) == ("defend",)

    def test_all_directions_for_move(self):
        for d in ("north", "south", "east", "west"):
            assert validate_action(("move", d)) == ("move", d)

    def test_all_directions_for_attack(self):
        for d in ("north", "south", "east", "west"):
            assert validate_action(("attack", d)) == ("attack", d)

    def test_list_accepted(self):
        assert validate_action(["move", "east"]) == ("move", "east")

    def test_rest_extra_args_ignored(self):
        result = validate_action(("rest",))
        assert result == ("rest",)

    def test_defend_extra_args_normalized(self):
        result = validate_action(("defend",))
        assert result == ("defend",)

    def test_none_input(self):
        assert validate_action(None) is None

    def test_string_input(self):
        assert validate_action("move north") is None

    def test_int_input(self):
        assert validate_action(42) is None

    def test_empty_tuple(self):
        assert validate_action(()) is None

    def test_invalid_action_type(self):
        assert validate_action(("fly", "north")) is None

    def test_move_missing_direction(self):
        assert validate_action(("move",)) is None

    def test_attack_missing_direction(self):
        assert validate_action(("attack",)) is None

    def test_move_invalid_direction(self):
        assert validate_action(("move", "up")) is None

    def test_attack_invalid_direction(self):
        assert validate_action(("attack", "diagonal")) is None


# --- execute_decide ---


class TestExecuteDecide:
    def test_successful_return(self):
        result = execute_decide(lambda s: ("rest",), {})
        assert result == ("rest",)

    def test_returns_complex_action(self):
        result = execute_decide(lambda s: ("move", "north"), {})
        assert result == ("move", "north")

    def test_state_passed_to_decide(self):
        def check_state(state):
            assert state["round"] == 5
            return ("rest",)
        result = execute_decide(check_state, {"round": 5})
        assert result == ("rest",)

    def test_exception_returns_none(self):
        def bad_bot(state):
            raise ValueError("oops")
        result = execute_decide(bad_bot, {})
        assert result is None

    def test_timeout_returns_none(self):
        def slow_bot(state):
            time.sleep(3)
            return ("rest",)
        result = execute_decide(slow_bot, {}, timeout=0.1)
        assert result is None

    def test_none_return_from_bot(self):
        result = execute_decide(lambda s: None, {})
        assert result is None

    def test_custom_timeout(self):
        def fast_bot(state):
            time.sleep(0.05)
            return ("move", "east")
        result = execute_decide(fast_bot, {}, timeout=0.5)
        assert result == ("move", "east")
