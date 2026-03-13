"""Tests for engine/sandbox.py — action validation, bot execution, timeout."""

import multiprocessing
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


# --- multiprocessing isolation ---


class TestSandboxIsolation:
    def test_state_not_mutated_by_bot(self):
        """Bot modifying state should not affect the caller's copy."""
        def mutating_bot(state):
            state["round"] = 999
            state["injected"] = "evil"
            return ("rest",)

        original_state = {"round": 1, "me": {"hp": 100}}
        result = execute_decide(mutating_bot, original_state)
        assert result == ("rest",)
        assert original_state["round"] == 1
        assert "injected" not in original_state
        assert original_state["me"]["hp"] == 100

    def test_nested_state_not_mutated(self):
        """Deep-copy should protect nested dicts too."""
        def nested_mutator(state):
            state["me"]["hp"] = 0
            state["me"]["new_key"] = "bad"
            return ("defend",)

        original_state = {"round": 1, "me": {"hp": 100, "energy": 50}}
        result = execute_decide(nested_mutator, original_state)
        assert result == ("defend",)
        assert original_state["me"]["hp"] == 100
        assert "new_key" not in original_state["me"]

    def test_process_terminates_on_timeout(self):
        """Timed-out process should be killed, not left running."""
        def infinite_bot(state):
            while True:
                pass

        before = len(multiprocessing.active_children())
        execute_decide(infinite_bot, {}, timeout=0.2)
        after = len(multiprocessing.active_children())
        assert after <= before


# --- error logging ---


class TestSandboxLogging:
    def test_timeout_logs_warning(self, caplog):
        """Timeout event should emit a warning log."""
        import logging

        def slow_bot(state):
            time.sleep(3)
            return ("rest",)

        with caplog.at_level(logging.WARNING, logger="engine.sandbox"):
            execute_decide(slow_bot, {}, timeout=0.1)

        assert any("timeout" in r.message.lower() for r in caplog.records), (
            f"Expected a warning containing 'timeout', got: {[r.message for r in caplog.records]}"
        )

    def test_exception_logs_warning(self, caplog):
        """Exception in bot should emit a warning log."""
        import logging

        def bad_bot(state):
            raise RuntimeError("bot exploded")

        with caplog.at_level(logging.WARNING, logger="engine.sandbox"):
            execute_decide(bad_bot, {}, timeout=2.0)

        assert any("exception" in r.message.lower() or "error" in r.message.lower() for r in caplog.records), (
            f"Expected a warning about exception/error, got: {[r.message for r in caplog.records]}"
        )
